from datetime import datetime, date, timezone, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, func, select

from app.database import AsyncSessionLocal
from app.models import (
    CleaningPaymentLedger,
    CleaningPaymentEntryType,
    CleaningRate,
    CleaningTask,
    CleaningTaskCheck,
    CleaningTaskMedia,
    CleaningTaskStatus,
    GlobalSetting,
    House,
    PaymentStatus,
    SupplyExpenseClaim,
    SupplyClaimStatus,
    User,
    UserRole,
)
from app.telegram.auth.admin import is_admin

# admin telegram_id → house_id (ждём новый тариф)
_awaiting_rate_input: dict[int, int] = {}
# admin telegram_id → "add" | "edit:{idx}" (ждём строку доп. услуги)
_awaiting_extra_input: dict[int, str] = {}

EXTRAS_KEY = "cleaning_extras"  # GlobalSetting key


def _parse_extras(value: str | None) -> list[tuple[str, int]]:
    """Парсит 'Название|300\\nДругая|500' → [(label, amount), ...]"""
    if not value:
        return []
    result = []
    for line in value.strip().splitlines():
        if "|" in line:
            parts = line.split("|", 1)
            try:
                result.append((parts[0].strip(), int(parts[1].strip())))
            except ValueError:
                pass
    return result


def _serialize_extras(extras: list[tuple[str, int]]) -> str:
    return "\n".join(f"{label}|{amount}" for label, amount in extras)

router = Router()


@router.message(Command("cleaner_tasks_overdue"))
async def cleaner_tasks_overdue(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningTask).where(
                CleaningTask.status.in_([CleaningTaskStatus.PENDING, CleaningTaskStatus.ESCALATED])
            ).order_by(CleaningTask.scheduled_date)
        )
        tasks = list(q.scalars().all())

    if not tasks:
        await message.answer("✅ Просроченных/проблемных задач нет")
        return

    lines = ["⚠️ <b>Проблемные задачи уборки</b>"]
    for t in tasks[:50]:
        lines.append(
            f"• #{t.id} | {t.scheduled_date.strftime('%d.%m')} | дом={t.house_id} | status={t.status.value} | cleaner_id={t.assigned_to_user_id or '-'}"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cleaner_task_assign"))
async def cleaner_task_assign(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("Формат: /cleaner_task_assign <task_id> <cleaner_user_id>")
        return

    task_id = int(parts[1])
    cleaner_user_id = int(parts[2])

    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        cleaner = await session.get(User, cleaner_user_id)
        if not task:
            await message.answer("Задача не найдена")
            return
        if not cleaner or cleaner.role != UserRole.CLEANER:
            await message.answer("Пользователь-уборщик не найден")
            return

        task.assigned_to_user_id = cleaner.id
        task.updated_at = datetime.now(timezone.utc)
        await session.commit()

    await message.answer(f"✅ Задача #{task_id} назначена на cleaner_user_id={cleaner_user_id}")


@router.message(Command("cleaner_task_close"))
async def cleaner_task_close(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) != 2:
        await message.answer("Формат: /cleaner_task_close <task_id>")
        return

    task_id = int(parts[1])

    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await message.answer("Задача не найдена")
            return

        task.status = CleaningTaskStatus.DONE
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        await session.commit()

    await message.answer(f"✅ Задача #{task_id} закрыта вручную")


@router.message(Command("cleaner_claims_open"))
async def cleaner_claims_open(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(SupplyExpenseClaim).where(
                SupplyExpenseClaim.status == SupplyClaimStatus.SUBMITTED
            ).order_by(SupplyExpenseClaim.created_at.desc())
        )
        claims = list(q.scalars().all())

    if not claims:
        await message.answer("✅ Непросмотренных чеков нет")
        return

    lines = ["🧾 <b>Чеки на согласование</b>"]
    for c in claims[:50]:
        lines.append(
            f"• claim #{c.id} | task={c.task_id or '-'} | cleaner={c.cleaner_user_id} | {float(c.amount_total):.2f} ₽ | {c.purchase_date.strftime('%d.%m.%Y')}"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cleaner_payout_details"))
async def cleaner_payout_details(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    period = parts[1] if len(parts) > 1 else datetime.now().strftime("%Y-%m")
    cleaner_id = int(parts[2]) if len(parts) > 2 else None

    async with AsyncSessionLocal() as session:
        stmt = select(CleaningPaymentLedger).where(CleaningPaymentLedger.period_key == period)
        if cleaner_id:
            stmt = stmt.where(CleaningPaymentLedger.cleaner_user_id == cleaner_id)

        q = await session.execute(stmt.order_by(CleaningPaymentLedger.created_at))
        rows = list(q.scalars().all())

    if not rows:
        await message.answer(f"За период {period} данных нет")
        return

    totals = {}
    lines = [f"💵 <b>Детализация выплат за {period}</b>"]
    for r in rows[:100]:
        cid = r.cleaner_user_id
        totals[cid] = totals.get(cid, 0.0) + float(r.amount)
        lines.append(
            f"• cleaner={cid} | task={r.task_id or '-'} | {r.entry_type.value} | {float(r.amount):.2f} ₽ | {r.status.value}"
        )

    lines.append("\n<b>Итоги:</b>")
    for cid, total in totals.items():
        lines.append(f"- cleaner {cid}: {total:.2f} ₽")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cleaner_payout_mark_paid"))
async def cleaner_payout_mark_paid(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("Формат: /cleaner_payout_mark_paid <YYYY-MM> <cleaner_user_id>")
        return

    period = parts[1]
    cleaner_id = int(parts[2])

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningPaymentLedger).where(
                and_(
                    CleaningPaymentLedger.period_key == period,
                    CleaningPaymentLedger.cleaner_user_id == cleaner_id,
                    CleaningPaymentLedger.status.in_([PaymentStatus.ACCRUED, PaymentStatus.APPROVED]),
                )
            )
        )
        rows = list(q.scalars().all())
        if not rows:
            await message.answer("Начисления не найдены")
            return

        now = datetime.now(timezone.utc)
        for r in rows:
            r.status = PaymentStatus.PAID
            r.paid_at = now

        await session.commit()

    await message.answer(f"✅ Отмечено как выплачено: period={period}, cleaner={cleaner_id}, записей={len(rows)}")


# ---------------------------------------------------------------------------
# Admin Cleaning Panel — inline buttons
# ---------------------------------------------------------------------------

STATUS_ICON = {
    CleaningTaskStatus.PENDING: "⏳",
    CleaningTaskStatus.ACCEPTED: "👍",
    CleaningTaskStatus.IN_PROGRESS: "🚿",
    CleaningTaskStatus.ESCALATED: "🚨",
    CleaningTaskStatus.DONE: "✅",
    CleaningTaskStatus.DECLINED: "❌",
    CleaningTaskStatus.CANCELLED: "🚫",
}


def _back_to_cleaning_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Уборки", callback_data="admin:cleaning")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")],
    ])


def _back_to_cleaner_kb(cleaner_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К уборщику", callback_data=f"admin:cleaning:cleaner:{cleaner_user_id}")],
        [InlineKeyboardButton(text="🧹 Уборки", callback_data="admin:cleaning")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")],
    ])


@router.callback_query(F.data == "admin:cleaning")
async def admin_cleaning_overview(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    since = date.today().replace(day=1)  # начало месяца

    async with AsyncSessionLocal() as session:
        cleaners_q = await session.execute(
            select(User).where(User.role == UserRole.CLEANER)
        )
        cleaners = list(cleaners_q.scalars().all())

        stats = {}
        for c in cleaners:
            total = await session.scalar(
                select(func.count()).where(
                    CleaningTask.assigned_to_user_id == c.id,
                    CleaningTask.scheduled_date >= since,
                )
            )
            done = await session.scalar(
                select(func.count()).where(
                    CleaningTask.assigned_to_user_id == c.id,
                    CleaningTask.scheduled_date >= since,
                    CleaningTask.status == CleaningTaskStatus.DONE,
                )
            )
            claims = await session.scalar(
                select(func.count()).where(
                    SupplyExpenseClaim.cleaner_user_id == c.id,
                    SupplyExpenseClaim.status == SupplyClaimStatus.SUBMITTED,
                )
            )
            stats[c.id] = (total or 0, done or 0, claims or 0)

    if not cleaners:
        await callback.message.edit_text(
            "🧹 <b>Уборки</b>\n\nУборщиков нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")]
            ]),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    month_name = since.strftime("%B %Y")
    lines = [f"🧹 <b>Уборки — {month_name}</b>\n"]
    rows = []
    for c in cleaners:
        total, done, claims = stats[c.id]
        claim_mark = f" | 🧾 {claims}" if claims else ""
        lines.append(f"👤 <b>{c.name}</b>: {done}/{total} уб.{claim_mark}")
        rows.append([InlineKeyboardButton(
            text=f"👤 {c.name} ({done}/{total})",
            callback_data=f"admin:cleaning:cleaner:{c.id}",
        )])

    rows.append([InlineKeyboardButton(text="⚙️ Настройки уборки", callback_data="admin:cleaning:settings")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")])
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cleaning:cleaner:"))
async def admin_cleaning_cleaner(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    cleaner_user_id = int(callback.data.split(":")[3])
    since = date.today() - timedelta(days=30)

    async with AsyncSessionLocal() as session:
        cleaner = await session.get(User, cleaner_user_id)
        if not cleaner:
            await callback.answer("Уборщик не найден", show_alert=True)
            return

        tasks_q = await session.execute(
            select(CleaningTask).where(
                CleaningTask.assigned_to_user_id == cleaner_user_id,
                CleaningTask.scheduled_date >= since,
            ).order_by(CleaningTask.scheduled_date.desc())
        )
        tasks = list(tasks_q.scalars().all())

        claims_q = await session.execute(
            select(SupplyExpenseClaim).where(
                SupplyExpenseClaim.cleaner_user_id == cleaner_user_id,
                SupplyExpenseClaim.status == SupplyClaimStatus.SUBMITTED,
            )
        )
        pending_claims = list(claims_q.scalars().all())

    lines = [f"👤 <b>{cleaner.name}</b> — задачи за 30 дней\n"]
    for t in tasks:
        icon = STATUS_ICON.get(t.status, "•")
        lines.append(f"{icon} #{t.id} | {t.scheduled_date.strftime('%d.%m')} | дом {t.house_id}")

    if pending_claims:
        lines.append(f"\n🧾 <b>Чеки на согласовании:</b> {len(pending_claims)} шт.")

    rows = [
        [InlineKeyboardButton(
            text=f"{STATUS_ICON.get(t.status,'•')} #{t.id} {t.scheduled_date.strftime('%d.%m')}",
            callback_data=f"admin:cleaning:task:{t.id}",
        )]
        for t in tasks[:15]
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Уборки", callback_data="admin:cleaning")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cleaning:task:") & ~F.data.contains(":photos"))
async def admin_cleaning_task(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    task_id = int(callback.data.split(":")[3])

    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        checks_q = await session.execute(
            select(CleaningTaskCheck).where(CleaningTaskCheck.task_id == task_id)
        )
        checks = list(checks_q.scalars().all())

        photo_count = await session.scalar(
            select(func.count()).where(CleaningTaskMedia.task_id == task_id)
        )

        claims_q = await session.execute(
            select(SupplyExpenseClaim).where(SupplyExpenseClaim.task_id == task_id)
        )
        claims = list(claims_q.scalars().all())

        cleaner = await session.get(User, task.assigned_to_user_id) if task.assigned_to_user_id else None

    checked = sum(1 for c in checks if c.is_checked)
    duration = ""
    if task.started_at and task.completed_at:
        mins = int((task.completed_at - task.started_at).total_seconds() / 60)
        duration = f"\n⏱ Длительность: {mins} мин."

    claims_line = ""
    if claims:
        total_amount = sum(float(c.amount_total) for c in claims)
        claims_line = f"\n🧾 Чеки: {len(claims)} шт. на {total_amount:.0f} ₽"

    text = (
        f"🧹 <b>Задача #{task.id}</b>\n"
        f"📅 {task.scheduled_date.strftime('%d.%m.%Y')} | 🏠 Дом {task.house_id}\n"
        f"📌 Статус: <b>{STATUS_ICON.get(task.status,'')} {task.status.value}</b>\n"
        f"👤 Уборщик: {cleaner.name if cleaner else '—'}"
        f"{duration}\n"
        f"☑️ Чеклист: {checked}/{len(checks)} пунктов"
        f"\n📸 Фото: {photo_count or 0}"
        f"{claims_line}"
    )

    rows = []
    if photo_count:
        rows.append([InlineKeyboardButton(
            text=f"📸 Посмотреть фото ({photo_count})",
            callback_data=f"admin:cleaning:task:{task_id}:photos",
        )])
    if claims:
        for c in claims[:3]:
            rows.append([InlineKeyboardButton(
                text=f"🧾 Чек #{c.id} — {float(c.amount_total):.0f} ₽ [{c.status.value}]",
                callback_data=f"admin:cleaning:claim:{c.id}",
            )])
    back_cleaner_id = task.assigned_to_user_id or 0
    rows.append([InlineKeyboardButton(text="⬅️ К уборщику", callback_data=f"admin:cleaning:cleaner:{back_cleaner_id}")])
    rows.append([InlineKeyboardButton(text="🧹 Уборки", callback_data="admin:cleaning")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin:cleaning:task:\d+:photos$"))
async def admin_cleaning_task_photos(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    task_id = int(callback.data.split(":")[3])

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningTaskMedia).where(
                CleaningTaskMedia.task_id == task_id,
                CleaningTaskMedia.media_type == "photo",
            ).order_by(CleaningTaskMedia.created_at)
        )
        photos = list(q.scalars().all())

    if not photos:
        await callback.answer("Фото нет", show_alert=True)
        return

    await callback.answer()
    for i, p in enumerate(photos, 1):
        try:
            await callback.message.answer_photo(
                p.telegram_file_id,
                caption=f"📸 Фото {i}/{len(photos)} — задача #{task_id}",
            )
        except Exception:
            pass

    await callback.message.answer(
        f"Показано {len(photos)} фото для задачи #{task_id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К задаче", callback_data=f"admin:cleaning:task:{task_id}")],
        ]),
    )


# ---------------------------------------------------------------------------
# Admin Cleaning Settings
# ---------------------------------------------------------------------------

async def _render_cleaning_settings(callback: CallbackQuery):
    async with AsyncSessionLocal() as s:
        houses_q = await s.execute(select(House).where(House.id != 4).order_by(House.id))
        houses = list(houses_q.scalars().all())

        rates_q = await s.execute(
            select(CleaningRate).where(CleaningRate.is_active.is_(True))
        )
        rates = {r.house_id: r for r in rates_q.scalars().all()}

        extras_setting = await s.get(GlobalSetting, EXTRAS_KEY)
        extras = _parse_extras(extras_setting.value if extras_setting else None)

    lines = ["⚙️ <b>Настройки уборки</b>\n", "<b>Тарифы по домикам:</b>"]
    for h in houses:
        rate = rates.get(h.id)
        amt = f"{int(rate.base_amount)} ₽" if rate else "не задан"
        lines.append(f"🏠 {h.name}: <b>{amt}</b>")

    lines.append("\n<b>Регулярные услуги (фикс. цена, без одобрения):</b>")
    if extras:
        for i, (label, amount) in enumerate(extras):
            lines.append(f"• {label}: <b>{amount} ₽</b>")
    else:
        lines.append("— пусто —")

    rows = []
    for h in houses:
        rate = rates.get(h.id)
        amt = f"{int(rate.base_amount)} ₽" if rate else "не задан"
        rows.append([InlineKeyboardButton(
            text=f"✏️ {h.name}: {amt}",
            callback_data=f"admin:cleaning:settings:rate:{h.id}",
        )])

    rows.append([InlineKeyboardButton(text="✏️ Регулярные услуги", callback_data="admin:cleaning:settings:extras")])
    rows.append([InlineKeyboardButton(text="⬅️ Уборки", callback_data="admin:cleaning")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:cleaning:settings")
async def admin_cleaning_settings(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await _render_cleaning_settings(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cleaning:settings:rate:"))
async def admin_cleaning_settings_rate_ask(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    house_id = int(callback.data.split(":")[4])
    _awaiting_rate_input[callback.from_user.id] = house_id

    async with AsyncSessionLocal() as s:
        house = await s.get(House, house_id)
        house_name = house.name if house else f"Дом {house_id}"

    await callback.message.edit_text(
        f"✏️ Введите новый тариф для <b>{house_name}</b> (₽/уборка, только число):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cleaning:settings")],
        ]),
    )
    await callback.answer()


@router.message(lambda m: m.from_user and m.from_user.id in _awaiting_rate_input and m.text)
async def admin_cleaning_settings_rate_save(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    tg_id = message.from_user.id
    house_id = _awaiting_rate_input.pop(tg_id, None)
    if house_id is None:
        return

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое положительное число.")
        _awaiting_rate_input[tg_id] = house_id
        return

    from decimal import Decimal
    async with AsyncSessionLocal() as s:
        # Деактивируем старый тариф
        old_q = await s.execute(
            select(CleaningRate).where(
                CleaningRate.house_id == house_id,
                CleaningRate.is_active.is_(True),
            )
        )
        for old in old_q.scalars().all():
            old.is_active = False
            old.active_to = date.today()

        s.add(CleaningRate(
            house_id=house_id,
            base_amount=Decimal(amount),
            active_from=date.today(),
            is_active=True,
        ))
        house = await s.get(House, house_id)
        house_name = house.name if house else f"Дом {house_id}"
        await s.commit()

    await message.answer(
        f"✅ Тариф для <b>{house_name}</b> установлен: <b>{amount} ₽</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Настройки", callback_data="admin:cleaning:settings")],
        ]),
    )


@router.callback_query(F.data == "admin:cleaning:settings:extras")
async def admin_cleaning_settings_extras(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    async with AsyncSessionLocal() as s:
        setting = await s.get(GlobalSetting, EXTRAS_KEY)
        extras = _parse_extras(setting.value if setting else None)

    rows = []
    for i, (label, amount) in enumerate(extras):
        rows.append([
            InlineKeyboardButton(text=f"✏️ {label} ({amount} ₽)", callback_data=f"admin:cleaning:settings:extra:edit:{i}"),
            InlineKeyboardButton(text="🗑", callback_data=f"admin:cleaning:settings:extra:del:{i}"),
        ])
    rows.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="admin:cleaning:settings:extra:add")])
    rows.append([InlineKeyboardButton(text="⬅️ Настройки", callback_data="admin:cleaning:settings")])

    text = "📋 <b>Регулярные услуги (фикс. цена)</b>\n\nЭти кнопки уборщица видит в задаче и нажимает сама — сумма начисляется сразу без одобрения.\n\nФормат: <code>Название | сумма</code>"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:cleaning:settings:extra:add")
async def admin_cleaning_settings_extra_add_ask(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _awaiting_extra_input[callback.from_user.id] = "add"
    await callback.message.edit_text(
        "➕ Введите услугу в формате:\n<code>Название | сумма</code>\n\nПример: <code>Отвезти белье в прачечную | 300</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cleaning:settings:extras")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cleaning:settings:extra:edit:"))
async def admin_cleaning_settings_extra_edit_ask(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    idx = callback.data.split(":")[-1]
    _awaiting_extra_input[callback.from_user.id] = f"edit:{idx}"
    await callback.message.edit_text(
        "✏️ Введите новое значение:\n<code>Название | сумма</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cleaning:settings:extras")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cleaning:settings:extra:del:"))
async def admin_cleaning_settings_extra_delete(callback: CallbackQuery):
    if not callback.from_user or not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    idx = int(callback.data.split(":")[-1])
    async with AsyncSessionLocal() as s:
        setting = await s.get(GlobalSetting, EXTRAS_KEY)
        extras = _parse_extras(setting.value if setting else None)
        if 0 <= idx < len(extras):
            extras.pop(idx)
        if setting:
            setting.value = _serialize_extras(extras)
        else:
            s.add(GlobalSetting(key=EXTRAS_KEY, value=_serialize_extras(extras)))
        await s.commit()

    await callback.answer("Удалено")
    await _render_cleaning_settings(callback)


@router.message(lambda m: m.from_user and m.from_user.id in _awaiting_extra_input and m.text)
async def admin_cleaning_settings_extra_save(message: Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return

    tg_id = message.from_user.id
    action = _awaiting_extra_input.pop(tg_id, None)
    if not action:
        return

    raw = message.text.strip()
    if "|" not in raw:
        await message.answer("❌ Нужен символ |. Пример: <code>Отвезти белье | 300</code>", parse_mode="HTML")
        _awaiting_extra_input[tg_id] = action
        return

    parts = raw.split("|", 1)
    try:
        label = parts[0].strip()
        amount = int(parts[1].strip())
        if amount <= 0 or not label:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат. Пример: <code>Отвезти белье | 300</code>", parse_mode="HTML")
        _awaiting_extra_input[tg_id] = action
        return

    async with AsyncSessionLocal() as s:
        setting = await s.get(GlobalSetting, EXTRAS_KEY)
        extras = _parse_extras(setting.value if setting else None)

        if action == "add":
            extras.append((label, amount))
        elif action.startswith("edit:"):
            idx = int(action.split(":", 1)[1])
            if 0 <= idx < len(extras):
                extras[idx] = (label, amount)

        new_val = _serialize_extras(extras)
        if setting:
            setting.value = new_val
        else:
            s.add(GlobalSetting(key=EXTRAS_KEY, value=new_val, description="Стандартные доп. услуги уборщицы"))
        await s.commit()

    await message.answer(
        f"✅ Сохранено: <b>{label}</b> — {amount} ₽",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Доп. услуги", callback_data="admin:cleaning:settings:extras")],
        ]),
    )
