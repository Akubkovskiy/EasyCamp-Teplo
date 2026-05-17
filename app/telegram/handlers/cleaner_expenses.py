import re
from datetime import date, datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, select

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import (
    CleaningPaymentEntryType,
    CleaningPaymentLedger,
    CleaningTask,
    CleaningTaskStatus,
    PaymentStatus,
    SupplyClaimStatus,
    SupplyExpenseClaim,
)
from app.telegram.auth.admin import UserRole, get_all_users, is_admin, resolve_user_db_id, is_cleaner

router = Router()

# Старый формат caption (обратная совместимость).
LEGACY_CLAIM_RE = re.compile(
    r"claim\s+task=(\d+)\s+amount=(\d+(?:\.\d{1,2})?)\s+items=(.+)", re.IGNORECASE
)

# Новый формат caption: первое число — сумма, остальное — описание.
# Примеры: "2000 ваза разбилась" | "1500₽ моющие средства" | "300 руб тряпки"
SIMPLE_CLAIM_RE = re.compile(
    r"^\s*(\d+(?:[.,]\d{1,2})?)\s*(?:р|руб|₽)?\s+(.+)$", re.IGNORECASE | re.DOTALL
)

# telegram_id уборщиц, ожидающих фото-чек (после нажатия кнопки «🧾 Расходники»)
_awaiting_receipt: set[int] = set()


def is_cleaner_awaiting_receipt(tg_id: int) -> bool:
    """Используется фильтром в cleaner_task_flow для отключения авто-привязки фото к задаче."""
    return tg_id in _awaiting_receipt


@router.callback_query(F.data == "cleaner:expense:new")
async def cleaner_expense_hint(callback: CallbackQuery):
    """Включаем режим ожидания чека. Уборщица отправляет фото с подписью «сумма описание»."""
    if callback.from_user:
        _awaiting_receipt.add(callback.from_user.id)

    text = (
        "🧾 <b>Прикрепить чек о расходах</b>\n\n"
        "Отправь сюда <b>фото чека</b> и в подписи укажи:\n"
        "<code>сумма описание</code>\n\n"
        "Примеры:\n"
        "• <code>2000 ваза разбилась — купила новую</code>\n"
        "• <code>1500 моющие средства, тряпки</code>\n"
        "• <code>800 газовый баллон</code>\n\n"
        "Чек можно прикрепить в любой момент — даже когда нет активной уборки.\n"
        "Если расход связан с конкретной уборкой, опишите это в тексте."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cleaner:expense:cancel")]]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "cleaner:expense:cancel")
async def cleaner_expense_cancel(callback: CallbackQuery):
    if callback.from_user:
        _awaiting_receipt.discard(callback.from_user.id)
    from app.telegram.handlers.cleaner import show_cleaner_menu
    await show_cleaner_menu(callback, callback.from_user.id)
    await callback.answer("Отменено")


def _is_receipt_photo(message: Message) -> bool:
    """Filter: фото от уборщицы которая нажала «🧾 Расходники»."""
    if not message.from_user or not message.photo:
        return False
    if not is_cleaner(message.from_user.id):
        return False
    return message.from_user.id in _awaiting_receipt


def _is_legacy_claim_photo(message: Message) -> bool:
    """Filter: старый формат `claim task=N amount=X items=...` (обратная совместимость)."""
    caption = message.caption or ""
    return bool(LEGACY_CLAIM_RE.search(caption))


async def _create_claim(
    *,
    cleaner_db_id: int,
    cleaner_tg: int,
    amount: float,
    items: str,
    file_id: str,
    task_id: int | None,
    bot,
) -> int:
    """Создать SupplyExpenseClaim и разослать админам на согласование."""
    async with AsyncSessionLocal() as session:
        claim = SupplyExpenseClaim(
            task_id=task_id,
            cleaner_user_id=cleaner_db_id,
            purchase_date=date.today(),
            amount_total=amount,
            items_json=items,
            receipt_photo_file_id=file_id,
            status=SupplyClaimStatus.SUBMITTED,
            created_at=datetime.now(timezone.utc),
        )
        session.add(claim)
        await session.commit()
        await session.refresh(claim)
        claim_id = claim.id

    task_label = f"Task #{task_id}" if task_id else "Без привязки к уборке"
    text = (
        f"🧾 <b>Новый чек расходников #{claim_id}</b>\n"
        f"{task_label}\n"
        f"Сумма: <b>{amount:.2f} ₽</b>\n"
        f"Позиции: {items}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"cleaner:claim:approve:{claim_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cleaner:claim:reject:{claim_id}"),
        ]]
    )

    users = await get_all_users()
    admin_ids = {u.telegram_id for u in users if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id}
    admin_ids.add(settings.telegram_chat_id)
    for aid in admin_ids:
        try:
            await bot.send_photo(aid, file_id, caption=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass

    return claim_id


@router.message(F.photo, _is_receipt_photo)
async def cleaner_receipt_submit(message: Message):
    """Новый flow: уборщица в режиме «ожидания чека», шлёт фото с подписью «сумма описание»."""
    cleaner_tg = message.from_user.id if message.from_user else None
    if not cleaner_tg:
        return

    _awaiting_receipt.discard(cleaner_tg)

    caption = (message.caption or "").strip()
    if not caption:
        # Сбрасываем флаг, но позволим повторить — подсказка с примером.
        _awaiting_receipt.add(cleaner_tg)
        await message.answer(
            "❌ Подпись отсутствует. Отправь фото ещё раз и в подписи укажи "
            "сумму и описание, например: <code>2000 ваза разбилась</code>",
            parse_mode="HTML",
        )
        return

    m = SIMPLE_CLAIM_RE.match(caption)
    if not m:
        _awaiting_receipt.add(cleaner_tg)
        await message.answer(
            "❌ Не распознал сумму. В подписи укажи сначала число, потом описание.\n"
            "Пример: <code>2000 ваза разбилась</code>",
            parse_mode="HTML",
        )
        return

    amount = float(m.group(1).replace(",", "."))
    items = m.group(2).strip()
    file_id = message.photo[-1].file_id

    async with AsyncSessionLocal() as session:
        cleaner_db_id = await resolve_user_db_id(session, cleaner_tg)
        if not cleaner_db_id:
            await message.answer(
                "❌ Вы не зарегистрированы как уборщица. Попросите администратора добавить вас."
            )
            return

        # Авто-привязка к активной IN_PROGRESS задаче, если есть. Иначе claim standalone.
        active_q = await session.execute(
            select(CleaningTask.id).where(
                CleaningTask.assigned_to_user_id == cleaner_db_id,
                CleaningTask.status == CleaningTaskStatus.IN_PROGRESS,
            ).order_by(CleaningTask.scheduled_date.desc()).limit(1)
        )
        active_task_id = active_q.scalar_one_or_none()

    claim_id = await _create_claim(
        cleaner_db_id=cleaner_db_id,
        cleaner_tg=cleaner_tg,
        amount=amount,
        items=items,
        file_id=file_id,
        task_id=active_task_id,
        bot=message.bot,
    )

    link_note = f"\nПривязан к задаче #{active_task_id}" if active_task_id else "\n(Без привязки к уборке)"
    await message.answer(f"✅ Чек #{claim_id} отправлен на согласование.{link_note}")


@router.message(F.photo, _is_legacy_claim_photo)
async def cleaner_legacy_claim_submit(message: Message):
    """Старый формат `claim task=N amount=X items=Y` — оставлен для обратной совместимости."""
    caption = message.caption or ""
    m = LEGACY_CLAIM_RE.search(caption)
    if not m:
        return

    task_id = int(m.group(1))
    amount = float(m.group(2))
    items = m.group(3).strip()
    file_id = message.photo[-1].file_id
    cleaner_tg = message.from_user.id if message.from_user else None

    if not cleaner_tg:
        return

    async with AsyncSessionLocal() as session:
        cleaner_db_id = await resolve_user_db_id(session, cleaner_tg)
        if not cleaner_db_id:
            await message.answer(
                "❌ Вы не зарегистрированы как уборщица. Попросите администратора добавить вас."
            )
            return

    claim_id = await _create_claim(
        cleaner_db_id=cleaner_db_id,
        cleaner_tg=cleaner_tg,
        amount=amount,
        items=items,
        file_id=file_id,
        task_id=task_id,
        bot=message.bot,
    )
    await message.answer(f"✅ Чек #{claim_id} отправлен на согласование (legacy формат, task #{task_id}).")


async def _review_claim(callback: CallbackQuery, claim_id: int, approve: bool):
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        claim = await session.get(SupplyExpenseClaim, claim_id)
        if not claim:
            await callback.answer("Claim не найден", show_alert=True)
            return

        if approve:
            claim.status = SupplyClaimStatus.APPROVED
            claim.reviewed_at = datetime.now(timezone.utc)

            period_key = claim.purchase_date.strftime("%Y-%m")
            session.add(
                CleaningPaymentLedger(
                    task_id=claim.task_id,
                    cleaner_user_id=claim.cleaner_user_id,
                    entry_type=CleaningPaymentEntryType.SUPPLY_REIMBURSEMENT,
                    amount=claim.amount_total,
                    period_key=period_key,
                    status=PaymentStatus.ACCRUED,
                    comment=f"Approved claim #{claim.id}",
                    created_at=datetime.now(timezone.utc),
                )
            )
        else:
            claim.status = SupplyClaimStatus.REJECTED
            claim.reviewed_at = datetime.now(timezone.utc)

        await session.commit()

    await callback.answer("Готово")
    try:
        status = "APPROVED" if approve else "REJECTED"
        await callback.message.edit_caption((callback.message.caption or "") + f"\n\nReview: {status}")
    except Exception:
        pass


@router.callback_query(F.data.startswith("cleaner:claim:approve:"))
async def approve_claim(callback: CallbackQuery):
    claim_id = int(callback.data.split(":")[3])
    await _review_claim(callback, claim_id, approve=True)


@router.callback_query(F.data.startswith("cleaner:claim:reject:"))
async def reject_claim(callback: CallbackQuery):
    claim_id = int(callback.data.split(":")[3])
    await _review_claim(callback, claim_id, approve=False)


@router.message(Command("cleaner_payout"))
async def cleaner_payout_report(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=1)
    period = parts[1].strip() if len(parts) > 1 else date.today().strftime("%Y-%m")

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningPaymentLedger).where(
                and_(
                    CleaningPaymentLedger.period_key == period,
                    CleaningPaymentLedger.status.in_([PaymentStatus.ACCRUED, PaymentStatus.APPROVED]),
                )
            )
        )
        rows = list(q.scalars().all())

    if not rows:
        await message.answer(f"За период {period} начислений нет")
        return

    totals: dict[int, float] = {}
    details = []
    for r in rows:
        totals[r.cleaner_user_id] = totals.get(r.cleaner_user_id, 0.0) + float(r.amount)
        details.append(
            f"• cleaner={r.cleaner_user_id} | task={r.task_id or '-'} | {r.entry_type.value} | {float(r.amount):.2f} ₽"
        )

    head = [f"💵 <b>Выплаты уборщицам за {period}</b>"]
    for cleaner_id, amount in totals.items():
        head.append(f"Итого cleaner {cleaner_id}: <b>{amount:.2f} ₽</b>")

    text = "\n".join(head) + "\n\n" + "\n".join(details[:50])
    await message.answer(text, parse_mode="HTML")
