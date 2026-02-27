"""Smoke verification for Cleaner v2 flow.

Checks:
1) task completion is blocked without checks/photos
2) task completion succeeds with checks/photos
3) cleaning_fee accrual created by rate
4) expense claim can be created and reimbursed into ledger
"""

import asyncio
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import (
    Booking,
    BookingSource,
    BookingStatus,
    CleaningPaymentEntryType,
    CleaningPaymentLedger,
    CleaningRate,
    CleaningTask,
    CleaningTaskStatus,
    House,
    PaymentStatus,
    SupplyClaimStatus,
    SupplyExpenseClaim,
    User,
    UserRole,
)
from app.services.cleaning_task_service import CleaningTaskService


async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        house = House(name="Дом A", description="", capacity=2)
        cleaner = User(telegram_id=123, role=UserRole.CLEANER, name="Клинер")
        session.add_all([house, cleaner])
        await session.flush()

        rate = CleaningRate(
            house_id=house.id,
            base_amount=Decimal("1000.00"),
            active_from=date.today(),
            is_active=True,
        )
        session.add(rate)

        booking = Booking(
            house_id=house.id,
            guest_name="Гость",
            guest_phone="+79990000000",
            check_in=date.today(),
            check_out=date.today(),
            guests_count=2,
            total_price=Decimal("5000.00"),
            advance_amount=Decimal("1000.00"),
            commission=Decimal("0"),
            prepayment_owner=Decimal("1000.00"),
            status=BookingStatus.CONFIRMED,
            source=BookingSource.DIRECT,
        )
        session.add(booking)
        await session.flush()

        task = CleaningTask(
            booking_id=booking.id,
            house_id=house.id,
            assigned_to_user_id=cleaner.id,
            scheduled_date=date.today(),
            status=CleaningTaskStatus.IN_PROGRESS,
        )
        session.add(task)
        await session.flush()

        await CleaningTaskService.ensure_default_checklist(session, task)

        blocked = await CleaningTaskService.transition_status(session, task, CleaningTaskStatus.DONE)
        assert blocked is False, "DONE must be blocked without checks/photos"

        for code, _, _ in CleaningTaskService.REQUIRED_CHECKS:
            await CleaningTaskService.toggle_check(session, task.id, code, True)
        await CleaningTaskService.add_photo(session, task.id, "photo1", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "photo2", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "photo3", cleaner.id)

        ok = await CleaningTaskService.transition_status(session, task, CleaningTaskStatus.DONE)
        assert ok is True, "DONE should pass with checks/photos"

        await session.commit()

        fees = (
            await session.execute(
                CleaningPaymentLedger.__table__.select().where(
                    CleaningPaymentLedger.task_id == task.id,
                    CleaningPaymentLedger.entry_type == CleaningPaymentEntryType.CLEANING_FEE,
                )
            )
        ).fetchall()
        assert len(fees) == 1, "cleaning fee accrual expected"

        claim = SupplyExpenseClaim(
            task_id=task.id,
            cleaner_user_id=cleaner.id,
            purchase_date=date.today(),
            amount_total=Decimal("2000.00"),
            items_json="губки,моющее",
            receipt_photo_file_id="receipt_photo",
            status=SupplyClaimStatus.APPROVED,
        )
        session.add(claim)
        await session.flush()

        session.add(
            CleaningPaymentLedger(
                task_id=task.id,
                cleaner_user_id=cleaner.id,
                entry_type=CleaningPaymentEntryType.SUPPLY_REIMBURSEMENT,
                amount=claim.amount_total,
                period_key=date.today().strftime("%Y-%m"),
                status=PaymentStatus.ACCRUED,
                comment=f"Approved claim #{claim.id}",
            )
        )
        await session.commit()

        print("OK: cleaner_v2 smoke flow passed")


if __name__ == "__main__":
    asyncio.run(main())
