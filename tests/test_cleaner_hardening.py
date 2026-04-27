"""Тесты Phase C10 (cleaner hardening): accrual, supply_alert,
booking cancel propagation. Используют in-memory SQLite + asyncio."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
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
    SupplyAlert,
    SupplyAlertStatus,
    User,
    UserRole,
)
from app.services.booking_service import BookingService
from app.services.cleaning_task_service import CleaningTaskService


async def _make_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return Session


async def _seed_house_cleaner(session, name: str = "H1") -> tuple[House, User]:
    house = House(name=name, description="", capacity=2)
    session.add(house)
    await session.flush()

    cleaner = User(telegram_id=111, role=UserRole.CLEANER, name="Cleaner")
    session.add(cleaner)
    await session.flush()
    return house, cleaner


async def _seed_booking_task(session, house: House, cleaner: User) -> tuple[Booking, CleaningTask]:
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
        assigned_to_user_id=cleaner.id,  # users.id, NOT telegram_id (C10.0)
        scheduled_date=date.today(),
        status=CleaningTaskStatus.IN_PROGRESS,
    )
    session.add(task)
    await session.flush()
    await CleaningTaskService.ensure_default_checklist(session, task)
    return booking, task


# -------------------------------------------------
# C10.6 — accrual idempotency
# -------------------------------------------------


@pytest.mark.asyncio
async def test_cleaning_fee_accrued_once_on_done():
    Session = await _make_session()
    async with Session() as session:
        house, cleaner = await _seed_house_cleaner(session)
        # активный тариф
        rate = CleaningRate(
            house_id=house.id,
            base_amount=Decimal("1000"),
            active_from=date.today(),
            is_active=True,
        )
        session.add(rate)
        await session.flush()

        booking, task = await _seed_booking_task(session, house, cleaner)

        # close required checks + 3 photos
        for code, _, _ in CleaningTaskService.REQUIRED_CHECKS:
            await CleaningTaskService.toggle_check(session, task.id, code, True)
        await CleaningTaskService.add_photo(session, task.id, "f1", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "f2", cleaner.id)
        await CleaningTaskService.add_photo(session, task.id, "f3", cleaner.id)

        ok = await CleaningTaskService.transition_status(
            session, task, CleaningTaskStatus.DONE, cleaner_user_id=cleaner.id
        )
        assert ok is True

        # one ledger entry created
        from sqlalchemy import select

        rows = (
            await session.execute(
                select(CleaningPaymentLedger).where(
                    CleaningPaymentLedger.task_id == task.id,
                    CleaningPaymentLedger.entry_type
                    == CleaningPaymentEntryType.CLEANING_FEE,
                )
            )
        ).scalars().all()
        assert len(rows) == 1
        assert rows[0].cleaner_user_id == cleaner.id  # users.id, not telegram_id
        assert rows[0].amount == Decimal("1000")
        assert rows[0].status == PaymentStatus.ACCRUED

        # repeat DONE transition does not create a duplicate
        await CleaningTaskService._accrue_cleaning_fee(session, task)
        rows2 = (
            await session.execute(
                select(CleaningPaymentLedger).where(
                    CleaningPaymentLedger.task_id == task.id,
                    CleaningPaymentLedger.entry_type
                    == CleaningPaymentEntryType.CLEANING_FEE,
                )
            )
        ).scalars().all()
        assert len(rows2) == 1


# -------------------------------------------------
# C10.1 — supply alerts: open idempotent + resolve
# -------------------------------------------------


@pytest.mark.asyncio
async def test_supply_alert_open_idempotent_and_resolve():
    Session = await _make_session()
    async with Session() as session:
        house, cleaner = await _seed_house_cleaner(session)
        booking, task = await _seed_booking_task(session, house, cleaner)

        a1 = await CleaningTaskService.open_supply_alert(
            session, task, items_json="моющее", reporter_user_id=cleaner.id
        )
        assert a1 is not None
        assert a1.status == SupplyAlertStatus.NEW

        # повторный open не создаёт дубль и возвращает существующий
        a2 = await CleaningTaskService.open_supply_alert(
            session, task, items_json=None, reporter_user_id=cleaner.id
        )
        assert a2.id == a1.id

        from sqlalchemy import select

        all_alerts = (
            await session.execute(
                select(SupplyAlert).where(SupplyAlert.task_id == task.id)
            )
        ).scalars().all()
        assert len(all_alerts) == 1
        assert all_alerts[0].items_json == "моющее"

        # resolve
        affected = await CleaningTaskService.resolve_supply_alerts(session, task)
        assert affected == 1
        await session.refresh(a1)
        assert a1.status == SupplyAlertStatus.RESOLVED
        assert a1.resolved_at is not None

        # повторный open после resolve создаёт НОВЫЙ alert
        a3 = await CleaningTaskService.open_supply_alert(
            session, task, items_json="губки", reporter_user_id=cleaner.id
        )
        assert a3.id != a1.id
        assert a3.status == SupplyAlertStatus.NEW


# -------------------------------------------------
# C10.2 — booking cancel propagates to task + ledger
# -------------------------------------------------


@pytest.mark.asyncio
async def test_booking_cancel_propagates_to_cleaning_task_and_ledger(monkeypatch):
    """cancel_booking должен:
    - перевести task в CANCELLED
    - погасить cleaning_fee ledger-entry, если уже было создано
    - не упасть, даже если уборщица не подвязана к telegram-боту
    """
    Session = await _make_session()
    async with Session() as session:
        house, cleaner = await _seed_house_cleaner(session)
        rate = CleaningRate(
            house_id=house.id,
            base_amount=Decimal("1000"),
            active_from=date.today(),
            is_active=True,
        )
        session.add(rate)
        await session.flush()

        booking, task = await _seed_booking_task(session, house, cleaner)

        # эмулируем что задача уже завершена и начисление было создано
        for code, _, _ in CleaningTaskService.REQUIRED_CHECKS:
            await CleaningTaskService.toggle_check(session, task.id, code, True)
        for fid in ["f1", "f2", "f3"]:
            await CleaningTaskService.add_photo(session, task.id, fid, cleaner.id)
        await CleaningTaskService.transition_status(
            session, task, CleaningTaskStatus.DONE, cleaner_user_id=cleaner.id
        )
        await session.commit()

        # patch out side-effects (Avito, sheets, bot notify)
        async def noop_unblock(_booking):
            return None

        async def noop_sheets():
            return None

        monkeypatch.setattr(BookingService, "_unblock_avito_dates", staticmethod(noop_unblock))
        monkeypatch.setattr(
            BookingService,
            "_safe_background_sheets_sync",
            classmethod(lambda cls: noop_sheets()),
        )

        ok = await BookingService.cancel_booking(session, booking.id)
        assert ok is True

        await session.refresh(booking)
        assert booking.status == BookingStatus.CANCELLED

        await session.refresh(task)
        # task.status should be CANCELLED. С учётом «терминальных» —
        # DONE является терминальным, поэтому при таком сценарии
        # каскад НЕ переводит DONE→CANCELLED. Это намеренно: задача
        # уже выполнена, мы только гасим начисление.
        assert task.status == CleaningTaskStatus.DONE  # terminal — оставлен

        from sqlalchemy import select

        ledger_rows = (
            await session.execute(
                select(CleaningPaymentLedger).where(
                    CleaningPaymentLedger.task_id == task.id
                )
            )
        ).scalars().all()
        assert len(ledger_rows) == 1
        assert ledger_rows[0].status == PaymentStatus.CANCELLED


@pytest.mark.asyncio
async def test_booking_cancel_propagates_to_active_task(monkeypatch):
    """Если задача ещё в IN_PROGRESS / PENDING / ACCEPTED — cancel должен
    перевести её в CANCELLED."""
    Session = await _make_session()
    async with Session() as session:
        house, cleaner = await _seed_house_cleaner(session)
        booking, task = await _seed_booking_task(session, house, cleaner)
        await session.commit()

        async def noop_unblock(_booking):
            return None

        async def noop_sheets():
            return None

        monkeypatch.setattr(BookingService, "_unblock_avito_dates", staticmethod(noop_unblock))
        monkeypatch.setattr(
            BookingService,
            "_safe_background_sheets_sync",
            classmethod(lambda cls: noop_sheets()),
        )

        ok = await BookingService.cancel_booking(session, booking.id)
        assert ok is True

        await session.refresh(task)
        assert task.status == CleaningTaskStatus.CANCELLED

        await session.refresh(booking)
        assert booking.status == BookingStatus.CANCELLED
