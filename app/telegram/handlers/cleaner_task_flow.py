import re
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, func, or_, select

from app.database import AsyncSessionLocal
from app.models import CleaningTask, CleaningTaskCheck, CleaningTaskMedia, CleaningTaskStatus
from app.services.cleaning_task_service import CleaningTaskService
from app.telegram.auth.admin import resolve_user_db_id

router = Router()

PHOTO_HINT_RE = re.compile(r"#task(\d+)")


def _task_actions_keyboard(task: CleaningTask) -> InlineKeyboardMarkup:
    rows = []
    if task.status == CleaningTaskStatus.PENDING:
        rows.append([
            InlineKeyboardButton(text="✅ Принять", callback_data=f"cleaner:task:accept:{task.id}"),
            InlineKeyboardButton(text="❌ Отказаться", callback_data=f"cleaner:task:decline:{task.id}"),
        ])
    elif task.status == CleaningTaskStatus.ACCEPTED:
        rows.append([
            InlineKeyboardButton(text="🚿 Начать уборку", callback_data=f"cleaner:task:start:{task.id}"),
        ])
    elif task.status == CleaningTaskStatus.IN_PROGRESS:
        rows.append([
            InlineKeyboardButton(text="☑️ Чеклист", callback_data=f"cleaner:task:checks:{task.id}"),
            InlineKeyboardButton(text="📸 Фото", callback_data=f"cleaner:task:photo:{task.id}"),
        ])
        rows.append([
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"cleaner:task:done:{task.id}"),
        ])

    rows.append([InlineKeyboardButton(text="⬅️ К задачам", callback_data="cleaner:tasks:today")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _get_tasks(user_id: int, days: int = 0) -> list[CleaningTask]:
    start = date.today()
    end = start + timedelta(days=days)

    # user_id here is telegram_id; resolve to DB PK for FK comparison
    db_user_id = await resolve_user_db_id(None, user_id)
    if db_user_id is None:
        return []

    async with AsyncSessionLocal() as session:
        date_filter = (
            and_(CleaningTask.scheduled_date >= start, CleaningTask.scheduled_date <= end)
            if days
            else (CleaningTask.scheduled_date == start)
        )
        stmt = select(CleaningTask).where(
            and_(
                or_(
                    CleaningTask.assigned_to_user_id == db_user_id,
                    and_(
                        CleaningTask.assigned_to_user_id.is_(None),
                        CleaningTask.status == CleaningTaskStatus.PENDING,
                    ),
                ),
                date_filter,
                CleaningTask.status.in_(
                    [
                        CleaningTaskStatus.PENDING,
                        CleaningTaskStatus.ACCEPTED,
                        CleaningTaskStatus.IN_PROGRESS,
                        CleaningTaskStatus.ESCALATED,
                        CleaningTaskStatus.DONE,
                    ]
                ),
            )
        ).order_by(CleaningTask.scheduled_date)
        result = await session.execute(stmt)
        return list(result.scalars().all())


@router.callback_query(F.data.startswith("cleaner:tasks:"))
async def cleaner_tasks_list(callback: CallbackQuery):
    mode = callback.data.split(":")[2]
    days = 7 if mode == "week" else 0
    tasks = await _get_tasks(callback.from_user.id, days=days)

    active = [t for t in tasks if t.status != CleaningTaskStatus.DONE]
    done = [t for t in tasks if t.status == CleaningTaskStatus.DONE]

    if not tasks:
        await callback.message.edit_text(
            "📌 Задач нет.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")]
            ]),
        )
        await callback.answer()
        return

    STATUS_ICON = {
        CleaningTaskStatus.PENDING: "⏳",
        CleaningTaskStatus.ACCEPTED: "👍",
        CleaningTaskStatus.IN_PROGRESS: "🚿",
        CleaningTaskStatus.ESCALATED: "🚨",
        CleaningTaskStatus.DONE: "✅",
    }

    lines = ["🧹 <b>Мои задачи</b>"]
    if active:
        lines.append("")
        for t in active:
            icon = STATUS_ICON.get(t.status, "•")
            lines.append(f"{icon} #{t.id} | {t.scheduled_date.strftime('%d.%m')}")
    if done:
        lines.append("\n<b>Выполненные:</b>")
        for t in done:
            lines.append(f"✅ #{t.id} | {t.scheduled_date.strftime('%d.%m')}")

    task_rows = [
        [InlineKeyboardButton(
            text=f"{STATUS_ICON.get(t.status, '•')} #{t.id} {t.scheduled_date.strftime('%d.%m')}",
            callback_data=f"cleaner:task:view:{t.id}"
        )]
        for t in tasks[:10]
    ]
    task_rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="cleaner:menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=task_rows)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
    await callback.answer()


async def _render_task_view(callback: CallbackQuery, task_id: int):
    """Отрисовывает карточку задачи в текущем сообщении. Принимает task_id явно
    чтобы не мутировать замороженный объект CallbackQuery."""
    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return
        photo_count = await session.scalar(
            select(func.count()).where(CleaningTaskMedia.task_id == task_id)
        )

    photo_line = f"\n📸 Фото: {photo_count}" if photo_count else ""
    text = (
        f"🧹 <b>Задача #{task.id}</b>\n"
        f"📅 Дата: {task.scheduled_date.strftime('%d.%m.%Y')}\n"
        f"🏠 Домик ID: {task.house_id}\n"
        f"📌 Статус: <b>{task.status.value}</b>"
        f"{photo_line}"
    )
    await callback.message.edit_text(text, reply_markup=_task_actions_keyboard(task), parse_mode="HTML")


@router.callback_query(F.data.startswith("cleaner:task:view:"))
async def cleaner_task_view(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[3])
    await _render_task_view(callback, task_id)
    await callback.answer()


async def _render_task_checks(callback: CallbackQuery, task_id: int):
    """Отрисовывает чеклист задачи. Принимает task_id явно."""
    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return
        await CleaningTaskService.ensure_default_checklist(session, task)
        q = await session.execute(
            select(CleaningTaskCheck).where(CleaningTaskCheck.task_id == task_id).order_by(CleaningTaskCheck.id)
        )
        checks = list(q.scalars().all())
        await session.commit()

    lines = [f"☑️ <b>Чеклист задачи #{task_id}</b>"]
    rows = []
    for c in checks:
        mark = "✅" if c.is_checked else "⬜"
        req = "*" if c.is_required else ""
        lines.append(f"{mark} {c.label}{req}")
        rows.append([
            InlineKeyboardButton(text=f"{mark} {c.code}", callback_data=f"cleaner:task:check:{task_id}:{c.code}")
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cleaner:task:view:{task_id}")])
    await callback.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")


@router.callback_query(F.data.startswith("cleaner:task:checks:"))
async def cleaner_task_checks(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[3])
    await _render_task_checks(callback, task_id)
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:task:check:"))
async def cleaner_toggle_check(callback: CallbackQuery):
    _, _, _, task_id_str, code = callback.data.split(":", 4)
    task_id = int(task_id_str)

    new_value: bool | None = None
    supply_alert_opened = False
    supply_alert_resolved = False
    house_id_for_alert = None

    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(CleaningTaskCheck).where(
                CleaningTaskCheck.task_id == task_id,
                CleaningTaskCheck.code == code,
            )
        )
        check = q.scalar_one_or_none()
        if not check:
            await callback.answer("Пункт не найден", show_alert=True)
            return

        new_value = not check.is_checked
        await CleaningTaskService.toggle_check(session, task_id, code, new_value)

        # Хук C10.1: код `need_purchase` → SupplyAlert (idempotent).
        if code == "need_purchase":
            task = await session.get(CleaningTask, task_id)
            if task:
                house_id_for_alert = task.house_id
                cleaner_db_id = await resolve_user_db_id(
                    session, callback.from_user.id
                )
                if new_value:
                    alert = await CleaningTaskService.open_supply_alert(
                        session,
                        task,
                        items_json=None,
                        reporter_user_id=cleaner_db_id,
                    )
                    supply_alert_opened = bool(alert)
                else:
                    affected = await CleaningTaskService.resolve_supply_alerts(
                        session, task
                    )
                    supply_alert_resolved = affected > 0

        await session.commit()

    if supply_alert_opened:
        await _notify_admins_supply_alert(
            callback.bot, task_id=task_id, house_id=house_id_for_alert
        )
        await callback.message.answer(
            "🧴 <b>Алерт отправлен администратору.</b>\n\n"
            "Если есть фото нехватки — отправьте его прямо в этот чат, "
            "оно прикрепится к задаче и администратор сможет его увидеть.",
            parse_mode="HTML",
        )

    if supply_alert_resolved:
        try:
            await callback.answer("Расходники отмечены как закрытые")
        except Exception:
            pass

    await _render_task_checks(callback, task_id)


async def _notify_admins_supply_alert(bot, *, task_id: int, house_id: int | None):
    """Шлёт всем админам уведомление о новом SupplyAlert."""
    from app.core.config import settings
    from app.models import UserRole
    from app.telegram.auth.admin import get_all_users

    users = await get_all_users()
    admin_ids = {
        u.telegram_id
        for u in users
        if u.role in {UserRole.ADMIN, UserRole.OWNER} and u.telegram_id
    }
    admin_ids.add(settings.telegram_chat_id)

    text = (
        "🧴 <b>Алерт: уборщица отметила нехватку расходников</b>\n\n"
        f"Задача: #{task_id}\n"
        f"Домик ID: {house_id if house_id is not None else '—'}\n\n"
        "Откройте задачу, уточните позиции и запланируйте закупку."
    )
    for aid in admin_ids:
        try:
            await bot.send_message(aid, text, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("cleaner:task:photo:"))
async def cleaner_task_photo_hint(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[3])
    await callback.message.edit_text(
        "📸 Отправь фото в этот чат с подписью вида: <code>#task{}</code>\n"
        "Можно отправить несколько фото по одному.".format(task_id),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cleaner:task:view:{task_id}")]]
        ),
    )
    await callback.answer()


def _is_task_photo(message: Message) -> bool:
    """Filter: фото с явным тегом `#taskN` в подписи."""
    caption = message.caption or ""
    return bool(PHOTO_HINT_RE.search(caption))


def _is_cleaner_photo(message: Message) -> bool:
    """Filter: фото от уборщицы БЕЗ тега — для авто-прикрепления к активной задаче.
    Гостевые фото (оплата и т.п.) не перехватываем: гости не в _db_cleaners."""
    from app.telegram.auth.admin import is_cleaner
    return (
        message.from_user is not None
        and is_cleaner(message.from_user.id)
        and not _is_task_photo(message)
    )


async def _get_active_task_id(telegram_id: int) -> int | None:
    """Возвращает id задачи IN_PROGRESS, назначенной на уборщицу, если есть."""
    db_user_id = await resolve_user_db_id(None, telegram_id)
    if db_user_id is None:
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CleaningTask.id).where(
                CleaningTask.assigned_to_user_id == db_user_id,
                CleaningTask.status == CleaningTaskStatus.IN_PROGRESS,
            ).order_by(CleaningTask.scheduled_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()


@router.message(F.photo, _is_task_photo)
async def cleaner_receive_photo(message: Message):
    caption = message.caption or ""
    m = PHOTO_HINT_RE.search(caption)
    if not m:
        return

    task_id = int(m.group(1))
    file_id = message.photo[-1].file_id

    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await message.answer("Задача не найдена")
            return
        cleaner_db_id = (
            await resolve_user_db_id(session, message.from_user.id)
            if message.from_user
            else None
        )
        await CleaningTaskService.add_photo(session, task_id, file_id, user_id=cleaner_db_id)
        await session.commit()

    await message.answer(f"✅ Фото прикреплено к задаче #{task_id}")


@router.message(F.photo, _is_cleaner_photo)
async def cleaner_receive_photo_auto(message: Message):
    """Любое фото от уборщицы без тега → к активной задаче IN_PROGRESS."""
    if not message.from_user:
        return

    task_id = await _get_active_task_id(message.from_user.id)
    if task_id is None:
        await message.answer("Нет активной задачи. Сначала нажмите «🚿 Начать уборку».")
        return

    file_id = message.photo[-1].file_id
    async with AsyncSessionLocal() as session:
        cleaner_db_id = await resolve_user_db_id(session, message.from_user.id)
        await CleaningTaskService.add_photo(session, task_id, file_id, user_id=cleaner_db_id)
        await session.commit()

    await message.answer(
        f"✅ Фото сохранено (задача #{task_id})\n\nМожно ещё добавить фото или завершить уборку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить уборку", callback_data=f"cleaner:task:done:{task_id}")],
            [InlineKeyboardButton(text="☑️ Чеклист", callback_data=f"cleaner:task:checks:{task_id}")],
            [InlineKeyboardButton(text="📋 Открыть задачу", callback_data=f"cleaner:task:view:{task_id}")],
        ]),
    )


async def _do_transition(callback: CallbackQuery, task_id: int, target: CleaningTaskStatus, decline_reason: str | None = None):
    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        # ВАЖНО: assigned_to_user_id — FK на users.id, передаём не telegram_id
        # а резолвленный PK. Если пользователь ещё не в БД — None,
        # тогда service оставит assigned_to_user_id как было (job
        # обычно уже назначил при генерации).
        cleaner_db_id = await resolve_user_db_id(session, callback.from_user.id)

        ok = await CleaningTaskService.transition_status(
            session,
            task,
            target,
            cleaner_user_id=cleaner_db_id,
            decline_reason=decline_reason,
        )
        if not ok:
            await callback.answer("Переход статуса недоступен или не выполнены условия", show_alert=True)
            return
        await session.commit()

    await callback.answer("Готово")
    await _render_task_view(callback, task_id)


@router.callback_query(F.data.startswith("cleaner:task:accept:"))
async def cleaner_task_accept(callback: CallbackQuery):
    await _do_transition(callback, int(callback.data.split(":")[3]), CleaningTaskStatus.ACCEPTED)


@router.callback_query(F.data.startswith("cleaner:task:decline:"))
async def cleaner_task_decline(callback: CallbackQuery):
    await _do_transition(callback, int(callback.data.split(":")[3]), CleaningTaskStatus.DECLINED, decline_reason="declined_in_ui")


@router.callback_query(F.data.startswith("cleaner:task:start:"))
async def cleaner_task_start(callback: CallbackQuery):
    await _do_transition(callback, int(callback.data.split(":")[3]), CleaningTaskStatus.IN_PROGRESS)


@router.callback_query(F.data.startswith("cleaner:task:done:"))
async def cleaner_task_done(callback: CallbackQuery):
    await _do_transition(callback, int(callback.data.split(":")[3]), CleaningTaskStatus.DONE)
