import re
from datetime import date, datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import (
    CleaningPaymentEntryType,
    CleaningPaymentLedger,
    PaymentStatus,
    SupplyClaimStatus,
    SupplyExpenseClaim,
)
from app.telegram.auth.admin import UserRole, get_all_users, is_admin

router = Router()

CLAIM_RE = re.compile(r"claim\s+task=(\d+)\s+amount=(\d+(?:\.\d{1,2})?)\s+items=(.+)", re.IGNORECASE)


@router.callback_query(F.data == "cleaner:expense:new")
async def cleaner_expense_hint(callback: CallbackQuery):
    text = (
        "🧾 Отправь фото чека с подписью:\n"
        "<code>claim task=123 amount=2000 items=губки,моющее,тряпки</code>\n\n"
        "Где task — id задачи уборки, amount — сумма чека."
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(F.photo)
async def cleaner_claim_submit(message: Message):
    caption = message.caption or ""
    m = CLAIM_RE.search(caption)
    if not m:
        return

    task_id = int(m.group(1))
    amount = float(m.group(2))
    items = m.group(3).strip()
    file_id = message.photo[-1].file_id
    cleaner_id = message.from_user.id if message.from_user else None

    if not cleaner_id:
        return

    async with AsyncSessionLocal() as session:
        claim = SupplyExpenseClaim(
            task_id=task_id,
            cleaner_user_id=cleaner_id,
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

    await message.answer(f"✅ Чек отправлен на согласование (claim #{claim.id})")

    text = (
        f"🧾 Новый чек расходников #{claim.id}\n"
        f"Task: #{task_id}\n"
        f"Сумма: {amount:.2f} ₽\n"
        f"Позиции: {items}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"cleaner:claim:approve:{claim.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cleaner:claim:reject:{claim.id}"),
        ]]
    )

    users = await get_all_users()
    admin_ids = {u.telegram_id for u in users if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id}
    admin_ids.add(settings.telegram_chat_id)
    for aid in admin_ids:
        try:
            await message.bot.send_photo(aid, file_id, caption=text, reply_markup=kb)
        except Exception:
            pass


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
