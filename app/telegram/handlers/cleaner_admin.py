from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.models import (
    CleaningPaymentLedger,
    CleaningTask,
    CleaningTaskStatus,
    PaymentStatus,
    SupplyExpenseClaim,
    SupplyClaimStatus,
    User,
    UserRole,
)
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
