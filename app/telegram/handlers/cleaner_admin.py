from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.models import CleaningTask, CleaningTaskStatus, SupplyExpenseClaim, SupplyClaimStatus, User, UserRole
from app.telegram.auth.admin import is_admin

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
