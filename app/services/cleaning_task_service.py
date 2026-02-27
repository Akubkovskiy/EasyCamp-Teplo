import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Booking,
    BookingStatus,
    CleaningPaymentEntryType,
    CleaningPaymentLedger,
    CleaningRate,
    CleaningTask,
    CleaningTaskStatus,
    PaymentStatus,
)

logger = logging.getLogger(__name__)


class CleaningTaskService:
    """Сервис задач уборки + первичный расчёт начислений."""

    ALLOWED_TRANSITIONS = {
        CleaningTaskStatus.PENDING: {
            CleaningTaskStatus.ACCEPTED,
            CleaningTaskStatus.DECLINED,
            CleaningTaskStatus.ESCALATED,
            CleaningTaskStatus.CANCELLED,
        },
        CleaningTaskStatus.ACCEPTED: {
            CleaningTaskStatus.IN_PROGRESS,
            CleaningTaskStatus.DECLINED,
            CleaningTaskStatus.ESCALATED,
            CleaningTaskStatus.CANCELLED,
        },
        CleaningTaskStatus.IN_PROGRESS: {
            CleaningTaskStatus.DONE,
            CleaningTaskStatus.ESCALATED,
            CleaningTaskStatus.CANCELLED,
        },
    }

    @staticmethod
    async def create_task_for_booking(db: AsyncSession, booking: Booking) -> CleaningTask | None:
        """Создаёт задачу уборки из брони (idempotent по booking_id)."""
        if booking.status not in {
            BookingStatus.CONFIRMED,
            BookingStatus.PAID,
            BookingStatus.CHECKING_IN,
            BookingStatus.CHECKED_IN,
            BookingStatus.COMPLETED,
        }:
            return None

        existing = await db.execute(
            select(CleaningTask).where(CleaningTask.booking_id == booking.id)
        )
        task = existing.scalar_one_or_none()
        if task:
            return task

        task = CleaningTask(
            booking_id=booking.id,
            house_id=booking.house_id,
            scheduled_date=booking.check_out,
            status=CleaningTaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(task)
        await db.flush()
        return task

    @classmethod
    def can_transition(cls, current: CleaningTaskStatus, target: CleaningTaskStatus) -> bool:
        if current == target:
            return True
        return target in cls.ALLOWED_TRANSITIONS.get(current, set())

    @classmethod
    async def transition_status(
        cls,
        db: AsyncSession,
        task: CleaningTask,
        target: CleaningTaskStatus,
        *,
        cleaner_user_id: int | None = None,
        decline_reason: str | None = None,
    ) -> bool:
        if not cls.can_transition(task.status, target):
            logger.warning("Invalid task transition %s -> %s (task=%s)", task.status, target, task.id)
            return False

        now = datetime.now(timezone.utc)
        task.status = target
        task.updated_at = now

        if target == CleaningTaskStatus.ACCEPTED:
            task.accepted_at = now
            if cleaner_user_id and not task.assigned_to_user_id:
                task.assigned_to_user_id = cleaner_user_id
        elif target == CleaningTaskStatus.IN_PROGRESS:
            task.started_at = now
        elif target == CleaningTaskStatus.DONE:
            task.completed_at = now
        elif target == CleaningTaskStatus.DECLINED:
            task.decline_reason = decline_reason
        elif target == CleaningTaskStatus.ESCALATED:
            task.escalated_at = now

        if target == CleaningTaskStatus.DONE:
            await cls._accrue_cleaning_fee(db, task)

        await db.flush()
        return True

    @staticmethod
    async def _accrue_cleaning_fee(db: AsyncSession, task: CleaningTask) -> None:
        """Начисляет сдельную оплату за уборку по тарифу домика."""
        existing = await db.execute(
            select(CleaningPaymentLedger).where(
                CleaningPaymentLedger.task_id == task.id,
                CleaningPaymentLedger.entry_type == CleaningPaymentEntryType.CLEANING_FEE,
                CleaningPaymentLedger.status != PaymentStatus.CANCELLED,
            )
        )
        if existing.scalar_one_or_none():
            return

        rate_q = await db.execute(
            select(CleaningRate)
            .where(
                CleaningRate.house_id == task.house_id,
                CleaningRate.is_active.is_(True),
                CleaningRate.active_from <= task.scheduled_date,
            )
            .order_by(CleaningRate.active_from.desc())
            .limit(1)
        )
        rate = rate_q.scalar_one_or_none()
        if not rate:
            logger.warning("No active cleaning rate for house_id=%s task=%s", task.house_id, task.id)
            return

        if not task.assigned_to_user_id:
            logger.warning("Task %s completed without assigned cleaner; fee skipped", task.id)
            return

        period_key = task.scheduled_date.strftime("%Y-%m")
        db.add(
            CleaningPaymentLedger(
                task_id=task.id,
                cleaner_user_id=task.assigned_to_user_id,
                entry_type=CleaningPaymentEntryType.CLEANING_FEE,
                amount=Decimal(rate.base_amount),
                period_key=period_key,
                status=PaymentStatus.ACCRUED,
                comment=f"Auto accrual for task #{task.id}",
                created_at=datetime.now(timezone.utc),
            )
        )
