"""Cleaner payments panel: balance, task history, payment requests, profile."""
from datetime import date
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models import (
    CleanerPaymentProfile,
    CleaningPaymentLedger,
    CleaningTask,
    CleaningTaskCheck,
    CleaningTaskMedia,
    CleaningTaskStatus,
    CleaningPaymentEntryType,
    PaymentStatus,
    SupplyExpenseClaim,
    SupplyClaimStatus,
    User,
    UserRole,
)
from app.telegram.auth.admin import resolve_user_db_id, is_cleaner

router = Router()

BANKS = ["Сбербанк", "Тинькофф", "ВТБ", "Альфа-Банк", "Райффайзен", "Другой"]

# telegram_id → ожидаем телефон
_awaiting_phone: set[int] = set()

# cleaner telegram_id → prompt_message_id
_awaiting_task_detail: dict[int, int] = {}

# cleaner telegram_id → list of photo message_ids to clean up
_cleaner_photo_msgs: dict[int, list[int]] = {}

# admin telegram_id → (task_id, cleaner_db_id) — ждём комментарий при оспаривании
_awaiting_adj_dispute: dict[int, tuple[int, int]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_profile(db_user_id: int):
    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(CleanerPaymentProfile).where(CleanerPaymentProfile.user_id == db_user_id)
        )
        return q.scalar_one_or_none()


async def _get_balance(db_user_id: int) -> tuple[Decimal, int, Decimal, Decimal]:
    """Возвращает (начислено_к_выплате, кол-во_уборок, возмещения, выплачено_в_этом_месяце)."""
    current_month = date.today().strftime("%Y-%m")
    async with AsyncSessionLocal() as s:
        # Начисления CLEANING_FEE ещё не выплаченные
        accrued = await s.scalar(
            select(func.sum(CleaningPaymentLedger.amount)).where(
                CleaningPaymentLedger.cleaner_user_id == db_user_id,
                CleaningPaymentLedger.entry_type == CleaningPaymentEntryType.CLEANING_FEE,
                CleaningPaymentLedger.status.in_([PaymentStatus.ACCRUED, PaymentStatus.APPROVED]),
            )
        ) or Decimal(0)

        task_count = await s.scalar(
            select(func.count()).where(
                CleaningPaymentLedger.cleaner_user_id == db_user_id,
                CleaningPaymentLedger.entry_type == CleaningPaymentEntryType.CLEANING_FEE,
                CleaningPaymentLedger.status.in_([PaymentStatus.ACCRUED, PaymentStatus.APPROVED]),
            )
        ) or 0

        # Одобренные возмещения расходников (ещё не выплачены)
        reimbursements = await s.scalar(
            select(func.sum(SupplyExpenseClaim.amount_total)).where(
                SupplyExpenseClaim.cleaner_user_id == db_user_id,
                SupplyExpenseClaim.status == SupplyClaimStatus.APPROVED,
            )
        ) or Decimal(0)

        # Выплачено в текущем календарном месяце
        paid_this_month = await s.scalar(
            select(func.sum(CleaningPaymentLedger.amount)).where(
                CleaningPaymentLedger.cleaner_user_id == db_user_id,
                CleaningPaymentLedger.status == PaymentStatus.PAID,
                CleaningPaymentLedger.period_key == current_month,
            )
        ) or Decimal(0)

    return Decimal(accrued), int(task_count), Decimal(reimbursements), Decimal(paid_this_month)


def _payments_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")],
    ])


# ---------------------------------------------------------------------------
# Main payments screen
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "cleaner:pay")
async def cleaner_pay_screen(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    accrued, task_count, reimbursements, paid_this_month = await _get_balance(db_user_id)
    total = accrued + reimbursements
    profile = await _get_profile(db_user_id)

    reimbursement_line = f"\n🧾 Возмещения расходников: {reimbursements:.0f} ₽" if reimbursements else ""
    paid_line = f"\n\n💳 Выплачено в этом месяце: {paid_this_month:.0f} ₽" if paid_this_month else ""

    profile_line = ""
    if profile and profile.sbp_phone:
        profile_line = f"\n\n🏦 Реквизиты: {profile.sbp_bank or '—'} · {profile.sbp_phone}"
    else:
        profile_line = "\n\n⚠️ Реквизиты не заданы — настройте перед запросом"

    text = (
        f"💰 <b>Выплаты</b>\n\n"
        f"🧹 Уборок к оплате: <b>{task_count}</b>\n"
        f"💵 Начислено: <b>{accrued:.0f} ₽</b>"
        f"{reimbursement_line}\n"
        f"📦 <b>Итого к получению: {total:.0f} ₽</b>"
        f"{paid_line}"
        f"{profile_line}"
    )

    rows = []
    if total > 0:
        rows.append([InlineKeyboardButton(
            text=f"💸 Запросить выплату {total:.0f} ₽",
            callback_data="cleaner:pay:request",
        )])
    rows.append([InlineKeyboardButton(text="📋 История уборок", callback_data="cleaner:pay:history")])
    rows.append([InlineKeyboardButton(text="📊 История платежей", callback_data="cleaner:pay:paid_history")])
    rows.append([InlineKeyboardButton(text="⚙️ Мои реквизиты", callback_data="cleaner:pay:profile")])
    rows.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="cleaner:menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await callback.answer()


# ---------------------------------------------------------------------------
# Task history
# ---------------------------------------------------------------------------

MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


@router.callback_query(F.data == "cleaner:pay:history")
async def cleaner_pay_history(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    tg_id = callback.from_user.id
    for msg_id in _cleaner_photo_msgs.pop(tg_id, []):
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception:
            pass

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        tasks_q = await s.execute(
            select(CleaningTask).where(
                CleaningTask.assigned_to_user_id == db_user_id,
                CleaningTask.status == CleaningTaskStatus.DONE,
            ).order_by(CleaningTask.scheduled_date.desc()).limit(60)
        )
        tasks = list(tasks_q.scalars().all())

        amounts: dict[int, Decimal] = {}
        for t in tasks:
            amt = await s.scalar(
                select(func.sum(CleaningPaymentLedger.amount)).where(
                    CleaningPaymentLedger.task_id == t.id,
                )
            )
            amounts[t.id] = Decimal(amt or 0)

    if not tasks:
        await callback.message.edit_text(
            "📋 <b>История уборок</b>\n\nВыполненных задач пока нет.",
            reply_markup=_payments_back_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    from collections import defaultdict
    by_month: dict[str, list] = defaultdict(list)
    for t in tasks:
        key = t.scheduled_date.strftime("%Y-%m")
        by_month[key].append(t)

    lines = ["📋 <b>История уборок</b>\n"]
    for month_key in sorted(by_month.keys(), reverse=True):
        month_tasks = by_month[month_key]
        year, mon = int(month_key[:4]), int(month_key[5:])
        month_total = sum(amounts[t.id] for t in month_tasks)
        lines.append(f"\n📅 <b>{MONTHS_RU[mon]} {year}</b> — {len(month_tasks)} уб. / {month_total:.0f} ₽")
        for t in month_tasks:
            amt = amounts[t.id]
            amt_str = f" {amt:.0f} ₽" if amt else ""
            lines.append(f"  ✅ #{t.id} | {t.scheduled_date.strftime('%d.%m')} | д.{t.house_id}{amt_str}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n…"

    rows = [
        [InlineKeyboardButton(text="🔍 Детали уборки", callback_data="cleaner:pay:history:ask_detail")],
        [InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "cleaner:pay:history:ask_detail")
async def cleaner_pay_history_ask_detail(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "🔍 <b>Детали уборки</b>\n\nВведите номер уборки (например: <code>23</code>)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cleaner:pay:history")],
        ]),
        parse_mode="HTML",
    )
    _awaiting_task_detail[callback.from_user.id] = callback.message.message_id
    await callback.answer()


@router.message(lambda m: m.from_user and m.from_user.id in _awaiting_task_detail and m.text)
async def cleaner_pay_history_detail_input(message: Message):
    from app.telegram.bot import bot
    tg_id = message.from_user.id
    prompt_msg_id = _awaiting_task_detail.pop(tg_id, None)

    raw = (message.text or "").strip().lstrip("#")
    try:
        await message.delete()
    except Exception:
        pass

    async def _reply(text, markup=None):
        if prompt_msg_id:
            await bot.edit_message_text(text, chat_id=message.chat.id, message_id=prompt_msg_id,
                                        reply_markup=markup, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")

    if not raw.isdigit():
        await _reply("❌ Введите число — номер уборки.")
        return

    task_id = int(raw)
    db_user_id = await resolve_user_db_id(None, tg_id)

    async with AsyncSessionLocal() as s:
        task = await s.get(CleaningTask, task_id)
        if not task or (db_user_id and task.assigned_to_user_id != db_user_id):
            await _reply(
                f"❌ Уборка #{task_id} не найдена.",
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ История уборок", callback_data="cleaner:pay:history")],
                ]),
            )
            return

        checks_q = await s.execute(
            select(CleaningTaskCheck).where(CleaningTaskCheck.task_id == task_id).order_by(CleaningTaskCheck.id)
        )
        checks = list(checks_q.scalars().all())

        media_q = await s.execute(
            select(CleaningTaskMedia).where(CleaningTaskMedia.task_id == task_id)
        )
        media = list(media_q.scalars().all())

        ledger_q = await s.execute(
            select(CleaningPaymentLedger).where(CleaningPaymentLedger.task_id == task_id)
        )
        ledger = list(ledger_q.scalars().all())

    duration = ""
    if task.started_at and task.completed_at:
        mins = int((task.completed_at - task.started_at).total_seconds() / 60)
        start = task.started_at.strftime("%H:%M")
        end = task.completed_at.strftime("%H:%M")
        duration = f"\n⏱ {start} → {end} ({mins} мин.)"

    checklist_lines = []
    for c in checks:
        mark = "✅" if c.is_checked else "⬜"
        checklist_lines.append(f"  {mark} {c.label}")

    notes_line = f"\n\n📝 Заметки: {task.notes}" if task.notes else ""

    pay_lines = []
    for e in ledger:
        type_label = {
            CleaningPaymentEntryType.CLEANING_FEE: "Уборка",
            CleaningPaymentEntryType.ADJUSTMENT: "Доп. работа",
            CleaningPaymentEntryType.SUPPLY_REIMBURSEMENT: "Расходники",
        }.get(e.entry_type, e.entry_type.value)
        status_mark = "✅" if e.status == PaymentStatus.PAID else "⏳"
        pay_lines.append(f"  {status_mark} {type_label}: {float(e.amount):.0f} ₽")

    lines = [
        f"🧹 <b>Уборка #{task.id}</b>",
        f"📅 {task.scheduled_date.strftime('%d.%m.%Y')} | 🏠 Дом {task.house_id}",
        f"📌 Статус: {task.status.value}" + duration,
    ]
    if checklist_lines:
        lines.append(f"\n☑️ <b>Чеклист:</b>")
        lines.extend(checklist_lines)
    if notes_line:
        lines.append(notes_line)
    if pay_lines:
        lines.append(f"\n💵 <b>Начисления:</b>")
        lines.extend(pay_lines)
    if media:
        lines.append(f"\n📸 Фото: {len(media)} шт. (отправлены ниже)")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ История уборок", callback_data="cleaner:pay:history")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")],
    ])
    await _reply("\n".join(lines), kb)

    # Отправляем фото отдельно
    if media:
        from aiogram.types import InputMediaPhoto
        photo_ids: list[int] = []
        if len(media) == 1:
            sent = await message.answer_photo(media[0].telegram_file_id)
            photo_ids = [sent.message_id]
        else:
            album = [InputMediaPhoto(media=m.telegram_file_id) for m in media[:10]]
            sent_list = await message.answer_media_group(album)
            photo_ids = [m.message_id for m in sent_list]
        if photo_ids:
            _cleaner_photo_msgs[tg_id] = photo_ids


# ---------------------------------------------------------------------------
# Paid history (actual transfers)
# ---------------------------------------------------------------------------

async def _load_paid_groups(db_user_id: int) -> list[tuple[str, Decimal, list]]:
    """Returns list of (day_key YYYY-MM-DD, total, entries) sorted newest-first."""
    from collections import defaultdict
    from datetime import datetime
    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(CleaningPaymentLedger).where(
                CleaningPaymentLedger.cleaner_user_id == db_user_id,
                CleaningPaymentLedger.status == PaymentStatus.PAID,
                CleaningPaymentLedger.paid_at.isnot(None),
            ).order_by(CleaningPaymentLedger.paid_at.desc()).limit(200)
        )
        entries = list(q.scalars().all())

    by_date: dict[str, list] = defaultdict(list)
    for e in entries:
        by_date[e.paid_at.strftime("%Y-%m-%d")].append(e)

    groups = []
    for day_key in sorted(by_date.keys(), reverse=True):
        day_entries = by_date[day_key]
        total = sum(Decimal(e.amount) for e in day_entries)
        groups.append((day_key, total, day_entries))
    return groups


@router.callback_query(F.data == "cleaner:pay:paid_history")
async def cleaner_pay_paid_history(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    groups = await _load_paid_groups(db_user_id)

    if not groups:
        await callback.message.edit_text(
            "📊 <b>История платежей</b>\n\nОплаченных переводов пока нет.",
            reply_markup=_payments_back_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    total_all = sum(g[1] for g in groups)
    rows = []
    for idx, (day_key, total, _) in enumerate(groups):
        num = f"#{idx + 1:02d}"
        d_fmt = day_key[8:10] + "." + day_key[5:7] + "." + day_key[:4]
        rows.append([InlineKeyboardButton(
            text=f"{num} — 💸 {d_fmt} — {total:.0f} ₽",
            callback_data=f"cleaner:pay:paid_detail:{day_key}",
        )])

    rows.append([InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")])

    text = f"📊 <b>История платежей</b>\n\n💰 Всего выплачено: <b>{total_all:.0f} ₽</b>\n\nНажмите на платёж для детализации:"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:pay:paid_detail:"))
async def cleaner_pay_paid_detail(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    day_key = callback.data[len("cleaner:pay:paid_detail:"):]
    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    groups = await _load_paid_groups(db_user_id)
    group = next(((d, t, e) for d, t, e in groups if d == day_key), None)
    if not group:
        await callback.answer("Платёж не найден", show_alert=True)
        return

    _, total, entries = group
    idx = next(i for i, (d, _, _) in enumerate(groups) if d == day_key)
    d_fmt = day_key[8:10] + "." + day_key[5:7] + "." + day_key[:4]
    num = f"#{idx + 1:02d}"

    lines = [f"💸 <b>Платёж {num} — {d_fmt}</b>\n<b>Итого: {total:.0f} ₽</b>\n"]
    for e in sorted(entries, key=lambda x: x.task_id or 0):
        type_label = {
            CleaningPaymentEntryType.CLEANING_FEE: "Уборка",
            CleaningPaymentEntryType.ADJUSTMENT: "Доп. работа",
            CleaningPaymentEntryType.SUPPLY_REIMBURSEMENT: "Расходники",
        }.get(e.entry_type, e.entry_type.value)
        task_ref = f" #{e.task_id}" if e.task_id else ""
        lines.append(f"  · {type_label}{task_ref}: {float(e.amount):.0f} ₽")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ История платежей", callback_data="cleaner:pay:paid_history")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Payment request
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "cleaner:pay:request")
async def cleaner_pay_request_confirm(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    profile = await _get_profile(db_user_id)
    if not profile or not profile.sbp_phone:
        await callback.message.edit_text(
            "⚠️ <b>Реквизиты не заданы</b>\n\nСначала укажите банк и номер телефона для СБП.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Задать реквизиты", callback_data="cleaner:pay:profile")],
                [InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")],
            ]),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    accrued, task_count, reimbursements, _ = await _get_balance(db_user_id)
    total = accrued + reimbursements

    text = (
        f"💸 <b>Подтвердите запрос на выплату</b>\n\n"
        f"🧹 Уборок: {task_count}\n"
        f"💵 Начислено: {accrued:.0f} ₽\n"
        + (f"🧾 Возмещения: {reimbursements:.0f} ₽\n" if reimbursements else "")
        + f"📦 <b>Итого: {total:.0f} ₽</b>\n\n"
        f"🏦 {profile.sbp_bank or '—'}\n"
        f"📱 {profile.sbp_phone}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить запрос", callback_data="cleaner:pay:request:send")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cleaner:pay")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "cleaner:pay:request:send")
async def cleaner_pay_request_send(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    accrued, task_count, reimbursements, _ = await _get_balance(db_user_id)
    total = accrued + reimbursements
    profile = await _get_profile(db_user_id)

    async with AsyncSessionLocal() as s:
        user = await s.get(User, db_user_id)
        cleaner_name = user.name if user else "—"

    if total <= 0:
        await callback.answer("Нечего запрашивать — баланс 0 ₽", show_alert=True)
        return

    # Уведомление всем админам
    from app.core.config import settings
    from app.telegram.auth.admin import get_all_users

    admin_users = await get_all_users()
    admin_ids = {u.telegram_id for u in admin_users if u.role in {UserRole.ADMIN}}
    admin_ids.add(settings.telegram_chat_id)

    period = date.today().strftime("%Y-%m")
    reimbursement_line = f"\n🧾 Возмещения: {reimbursements:.0f} ₽" if reimbursements else ""
    profile_line = ""
    if profile and profile.sbp_phone:
        profile_line = f"\n\n🏦 {profile.sbp_bank or '—'}\n📱 {profile.sbp_phone}"

    admin_text = (
        f"💸 <b>Запрос на выплату</b>\n\n"
        f"👤 {cleaner_name}\n"
        f"📅 Период: {period}\n"
        f"🧹 Уборок: {task_count}\n"
        f"💵 Начислено: {accrued:.0f} ₽"
        f"{reimbursement_line}\n"
        f"📦 <b>Итого: {total:.0f} ₽</b>"
        f"{profile_line}"
    )
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Перевёл", callback_data=f"admin:pay:approve:{db_user_id}:{period}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin:pay:reject:{db_user_id}:{period}"),
        ]
    ])

    for aid in admin_ids:
        try:
            await callback.bot.send_message(aid, admin_text, reply_markup=admin_kb, parse_mode="HTML")
        except Exception:
            pass

    await callback.message.edit_text(
        "✅ <b>Запрос отправлен администратору.</b>\n\nВы получите уведомление после подтверждения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Admin approves / rejects payment
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("admin:pay:approve:"))
async def admin_pay_approve(callback: CallbackQuery):
    from app.telegram.auth.admin import is_admin
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, _, _, cleaner_user_id_str, period = callback.data.split(":", 4)
    cleaner_user_id = int(cleaner_user_id_str)

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(CleaningPaymentLedger).where(
                CleaningPaymentLedger.cleaner_user_id == cleaner_user_id,
                CleaningPaymentLedger.status.in_([PaymentStatus.ACCRUED, PaymentStatus.APPROVED]),
            )
        )
        entries = list(q.scalars().all())

        claims_q = await s.execute(
            select(SupplyExpenseClaim).where(
                SupplyExpenseClaim.cleaner_user_id == cleaner_user_id,
                SupplyExpenseClaim.status == SupplyClaimStatus.APPROVED,
            )
        )
        claims = list(claims_q.scalars().all())

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        total = Decimal(0)

        for e in entries:
            e.status = PaymentStatus.PAID
            e.paid_at = now
            total += Decimal(e.amount)

        for c in claims:
            c.status = SupplyClaimStatus.PAID
            c.paid_at = now
            total += Decimal(c.amount_total)

        cleaner = await s.get(User, cleaner_user_id)
        cleaner_tg_id = cleaner.telegram_id if cleaner else None
        await s.commit()

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Оплачено {total:.0f} ₽</b> — {callback.from_user.first_name}",
        parse_mode="HTML",
    )
    await callback.answer(f"Отмечено как оплачено: {total:.0f} ₽")

    if cleaner_tg_id:
        try:
            await callback.bot.send_message(
                cleaner_tg_id,
                f"💸 <b>Оплата переведена!</b>\n\n"
                f"💵 Сумма: <b>{total:.0f} ₽</b>\n"
                f"Проверьте поступление на реквизиты СБП.",
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin:pay:reject:"))
async def admin_pay_reject(callback: CallbackQuery):
    from app.telegram.auth.admin import is_admin
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, _, _, cleaner_user_id_str, period = callback.data.split(":", 4)
    cleaner_user_id = int(cleaner_user_id_str)

    async with AsyncSessionLocal() as s:
        cleaner = await s.get(User, cleaner_user_id)
        cleaner_tg_id = cleaner.telegram_id if cleaner else None

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>Отклонено</b> — {callback.from_user.first_name}",
        parse_mode="HTML",
    )
    await callback.answer("Запрос отклонён")

    if cleaner_tg_id:
        try:
            await callback.bot.send_message(
                cleaner_tg_id,
                "❌ <b>Запрос на выплату отклонён администратором.</b>\n\n"
                "Свяжитесь с администратором для уточнения.",
                parse_mode="HTML",
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Payment profile
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "cleaner:pay:profile")
async def cleaner_pay_profile(callback: CallbackQuery):
    if not callback.from_user or not is_cleaner(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    profile = await _get_profile(db_user_id) if db_user_id else None

    bank = profile.sbp_bank if profile else "не задан"
    phone = profile.sbp_phone if profile else "не задан"

    text = (
        f"⚙️ <b>Реквизиты для выплат (СБП)</b>\n\n"
        f"🏦 Банк: <b>{bank}</b>\n"
        f"📱 Телефон: <b>{phone}</b>"
    )
    rows = [
        [InlineKeyboardButton(text="🏦 Изменить банк", callback_data="cleaner:pay:profile:bank")],
        [InlineKeyboardButton(text="📱 Изменить телефон", callback_data="cleaner:pay:profile:phone")],
        [InlineKeyboardButton(text="⬅️ Выплаты", callback_data="cleaner:pay")],
    ]
    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cleaner:pay:profile:bank")
async def cleaner_pay_profile_bank_choose(callback: CallbackQuery):
    rows = [
        [InlineKeyboardButton(text=b, callback_data=f"cleaner:pay:profile:bank:{b}")]
        for b in BANKS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Реквизиты", callback_data="cleaner:pay:profile")])
    await callback.message.edit_text(
        "🏦 Выберите банк:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:pay:profile:bank:"))
async def cleaner_pay_profile_bank_save(callback: CallbackQuery):
    bank = callback.data[len("cleaner:pay:profile:bank:"):]
    db_user_id = await resolve_user_db_id(None, callback.from_user.id)
    if not db_user_id:
        await callback.answer("Ошибка", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(CleanerPaymentProfile).where(CleanerPaymentProfile.user_id == db_user_id)
        )
        profile = q.scalar_one_or_none()
        if profile:
            profile.sbp_bank = bank
        else:
            s.add(CleanerPaymentProfile(user_id=db_user_id, sbp_bank=bank))
        await s.commit()

    await callback.answer(f"Банк сохранён: {bank}")
    # Вернуть в профиль через edit
    await callback.message.edit_text(
        f"✅ Банк сохранён: <b>{bank}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Реквизиты", callback_data="cleaner:pay:profile")],
        ]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cleaner:pay:profile:phone")
async def cleaner_pay_profile_phone_ask(callback: CallbackQuery):
    if callback.from_user:
        _awaiting_phone.add(callback.from_user.id)
    await callback.message.edit_text(
        "📱 Отправьте номер телефона для СБП в формате <code>+7XXXXXXXXXX</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cleaner:pay:profile")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(lambda m: m.from_user and m.from_user.id in _awaiting_phone and m.text)
async def cleaner_pay_profile_phone_save(message: Message):
    phone = (message.text or "").strip()
    if not phone.startswith("+7") or len(phone) < 11:
        await message.answer("❌ Неверный формат. Отправьте номер в виде <code>+7XXXXXXXXXX</code>", parse_mode="HTML")
        return

    _awaiting_phone.discard(message.from_user.id)
    db_user_id = await resolve_user_db_id(None, message.from_user.id)
    if not db_user_id:
        return

    async with AsyncSessionLocal() as s:
        q = await s.execute(
            select(CleanerPaymentProfile).where(CleanerPaymentProfile.user_id == db_user_id)
        )
        profile = q.scalar_one_or_none()
        if profile:
            profile.sbp_phone = phone
        else:
            s.add(CleanerPaymentProfile(user_id=db_user_id, sbp_phone=phone))
        await s.commit()

    await message.answer(
        f"✅ Телефон сохранён: <b>{phone}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Реквизиты", callback_data="cleaner:pay:profile")],
        ]),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Admin: approve / dispute extra adjustment payment
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("admin:pay:adj_approve:"))
async def admin_pay_adj_approve(callback: CallbackQuery):
    from datetime import datetime, timezone
    from app.telegram.auth.admin import is_admin
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    task_id = int(parts[3])
    cleaner_db_id = int(parts[4])
    amount = Decimal(parts[5])

    period_key = date.today().strftime("%Y-%m")
    async with AsyncSessionLocal() as s:
        s.add(CleaningPaymentLedger(
            task_id=task_id,
            cleaner_user_id=cleaner_db_id,
            entry_type=CleaningPaymentEntryType.ADJUSTMENT,
            amount=amount,
            period_key=period_key,
            status=PaymentStatus.ACCRUED,
            comment=f"Доп. работа по задаче #{task_id} — одобрено {callback.from_user.first_name}",
            created_at=datetime.now(timezone.utc),
        ))
        cleaner = await s.get(User, cleaner_db_id)
        cleaner_tg_id = cleaner.telegram_id if cleaner else None
        await s.commit()

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Одобрено {amount:.0f} ₽</b> — {callback.from_user.first_name}",
        parse_mode="HTML",
    )
    await callback.answer(f"Одобрено: {amount:.0f} ₽")

    if cleaner_tg_id:
        try:
            await callback.bot.send_message(
                cleaner_tg_id,
                f"✅ <b>Доп. оплата одобрена!</b>\n\n"
                f"🧹 Задача #{task_id}\n"
                f"💵 Сумма: <b>{amount:.0f} ₽</b>\n\n"
                f"Отражено в разделе «Мои выплаты».",
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin:pay:adj_reject:"))
async def admin_pay_adj_reject(callback: CallbackQuery):
    from app.telegram.auth.admin import is_admin
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    task_id = int(parts[3])
    cleaner_db_id = int(parts[4])
    _awaiting_adj_dispute[callback.from_user.id] = (task_id, cleaner_db_id)

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>Оспорить — укажите причину или предложите другую сумму:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Просто отклонить (без комментария)", callback_data=f"admin:pay:adj_reject_confirm:{task_id}:{cleaner_db_id}")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pay:adj_reject_confirm:"))
async def admin_pay_adj_reject_confirm(callback: CallbackQuery):
    from app.telegram.auth.admin import is_admin
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    task_id = int(parts[3])
    cleaner_db_id = int(parts[4])
    _awaiting_adj_dispute.pop(callback.from_user.id, None)

    async with AsyncSessionLocal() as s:
        cleaner = await s.get(User, cleaner_db_id)
        cleaner_tg_id = cleaner.telegram_id if cleaner else None

    await callback.message.edit_text(
        callback.message.text.split("\n\n❌")[0] + f"\n\n❌ <b>Отклонено</b> — {callback.from_user.first_name}",
        parse_mode="HTML",
    )
    await callback.answer("Отклонено")

    if cleaner_tg_id:
        try:
            await callback.bot.send_message(
                cleaner_tg_id,
                f"❌ <b>Запрос доп. оплаты отклонён.</b>\n\n"
                f"🧹 Задача #{task_id}\n\n"
                f"Свяжитесь с администратором для уточнения.",
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.message(lambda m: m.from_user and m.from_user.id in _awaiting_adj_dispute and m.text)
async def admin_pay_adj_dispute_comment(message: Message):
    from datetime import datetime, timezone
    from app.telegram.auth.admin import is_admin
    if not message.from_user or not is_admin(message.from_user.id):
        return

    tg_id = message.from_user.id
    state = _awaiting_adj_dispute.pop(tg_id, None)
    if not state:
        return

    task_id, cleaner_db_id = state
    comment = message.text.strip()

    # Проверяем: это число (встречная сумма) или текст (причина отказа)?
    try:
        counter_amount = Decimal(comment.replace(",", ".").split(".")[0])
        is_counter = counter_amount > 0
    except Exception:
        is_counter = False

    async with AsyncSessionLocal() as s:
        if is_counter:
            period_key = date.today().strftime("%Y-%m")
            s.add(CleaningPaymentLedger(
                task_id=task_id,
                cleaner_user_id=cleaner_db_id,
                entry_type=CleaningPaymentEntryType.ADJUSTMENT,
                amount=counter_amount,
                period_key=period_key,
                status=PaymentStatus.ACCRUED,
                comment=f"Доп. работа #{task_id} — встречное предложение {message.from_user.first_name}",
                created_at=datetime.now(timezone.utc),
            ))
        cleaner = await s.get(User, cleaner_db_id)
        cleaner_tg_id = cleaner.telegram_id if cleaner else None
        await s.commit()

    if is_counter:
        await message.answer(f"✅ Начислено встречное предложение: {counter_amount:.0f} ₽ по задаче #{task_id}", parse_mode="HTML")
        cleaner_msg = (
            f"💰 <b>Администратор предложил другую сумму</b>\n\n"
            f"🧹 Задача #{task_id}\n"
            f"💵 Начислено: <b>{counter_amount:.0f} ₽</b>"
        )
    else:
        await message.answer(f"Запрос отклонён с комментарием: {comment}")
        cleaner_msg = (
            f"❌ <b>Запрос доп. оплаты отклонён.</b>\n\n"
            f"🧹 Задача #{task_id}\n"
            f"💬 Комментарий: {comment}"
        )

    if cleaner_tg_id:
        try:
            await message.bot.send_message(cleaner_tg_id, cleaner_msg, parse_mode="HTML")
        except Exception:
            pass
