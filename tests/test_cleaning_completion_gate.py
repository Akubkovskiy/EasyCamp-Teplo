from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import (
    Booking,
    BookingSource,
    BookingStatus,
    CleaningTask,
    CleaningTaskStatus,
    House,
    User,
    UserRole,
)
from app.services.cleaning_task_service import CleaningTaskService


@pytest.mark.asyncio
async def test_done_blocked_without_checks_and_photos():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        house = House(name="H1", description="", capacity=2)
        session.add(house)
        await session.flush()

        cleaner = User(telegram_id=111, role=UserRole.CLEANER, name="Cleaner")
        session.add(cleaner)
        await session.flush()

        booking = Booking(
            house_id=house.id,
            guest_name="Guest",
            guest_phone="+79990000000",
            check_in=date.today(),
            check_out=date.today(),
            guests_count=2,
            total_price=Decimal("1000"),
            advance_amount=Decimal("0"),
            commission=Decimal("0"),
            prepayment_owner=Decimal("0"),
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
        ok = await CleaningTaskService.transition_status(session, task, CleaningTaskStatus.DONE)
        assert ok is False

        # Закрываем все required checks
        for code, _, _ in CleaningTaskService.REQUIRED_CHECKS:
            await CleaningTaskService.toggle_check(session, task.id, code, True)

        # Добавляем 3 фото
        await CleaningTaskService.add_photo(session, task.id, "f1", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "f2", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "f3", cleaner.id)

        ok2 = await CleaningTaskService.transition_status(session, task, CleaningTaskStatus.DONE)
        assert ok2 is True
