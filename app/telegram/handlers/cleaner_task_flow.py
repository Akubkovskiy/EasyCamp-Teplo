import re
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.models import CleaningTask, CleaningTaskCheck, CleaningTaskStatus
from app.services.cleaning_task_service import CleaningTaskService

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

    async with AsyncSessionLocal() as session:
        date_filter = (
            and_(CleaningTask.scheduled_date >= start, CleaningTask.scheduled_date <= end)
            if days
            else (CleaningTask.scheduled_date == start)
        )
        stmt = select(CleaningTask).where(
            and_(
                CleaningTask.assigned_to_user_id == user_id,
                date_filter,
                CleaningTask.status.in_(
                    [
                        CleaningTaskStatus.PENDING,
                        CleaningTaskStatus.ACCEPTED,
                        CleaningTaskStatus.IN_PROGRESS,
                        CleaningTaskStatus.ESCALATED,
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

    if not tasks:
        await callback.message.edit_text("📌 Активных задач нет.")
        await callback.answer()
        return

    lines = ["🧹 <b>Мои задачи</b>\n"]
    for t in tasks:
        lines.append(f"• #{t.id} | {t.scheduled_date.strftime('%d.%m')} | {t.status.value}")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Открыть #{t.id}", callback_data=f"cleaner:task:view:{t.id}")]
            for t in tasks[:10]
        ]
    )
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:task:view:"))
async def cleaner_task_view(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[3])
    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

    text = (
        f"🧹 <b>Задача #{task.id}</b>\n"
        f"📅 Дата: {task.scheduled_date.strftime('%d.%m.%Y')}\n"
        f"🏠 Домик ID: {task.house_id}\n"
        f"📌 Статус: <b>{task.status.value}</b>"
    )
    await callback.message.edit_text(text, reply_markup=_task_actions_keyboard(task), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:task:checks:"))
async def cleaner_task_checks(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[3])
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
    await callback.answer()


@router.callback_query(F.data.startswith("cleaner:task:check:"))
async def cleaner_toggle_check(callback: CallbackQuery):
    _, _, _, task_id_str, code = callback.data.split(":", 4)
    task_id = int(task_id_str)

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
        await CleaningTaskService.toggle_check(session, task_id, code, not check.is_checked)
        await session.commit()

    callback.data = f"cleaner:task:checks:{task_id}"
    await cleaner_task_checks(callback)


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


@router.message(F.photo)
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
        await CleaningTaskService.add_photo(session, task_id, file_id, user_id=message.from_user.id if message.from_user else None)
        await session.commit()

    await message.answer(f"✅ Фото прикреплено к задаче #{task_id}")


async def _do_transition(callback: CallbackQuery, task_id: int, target: CleaningTaskStatus, decline_reason: str | None = None):
    async with AsyncSessionLocal() as session:
        task = await session.get(CleaningTask, task_id)
        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        ok = await CleaningTaskService.transition_status(
            session,
            task,
            target,
            cleaner_user_id=callback.from_user.id,
            decline_reason=decline_reason,
        )
        if not ok:
            await callback.answer("Переход статуса недоступен или не выполнены условия", show_alert=True)
            return
        await session.commit()

    await callback.answer("Готово")
    callback.data = f"cleaner:task:view:{task_id}"
    await cleaner_task_view(callback)


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
