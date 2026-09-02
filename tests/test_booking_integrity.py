"""Integration tests for the durable booking-creation boundary."""

import asyncio
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Booking, BookingSource, BookingStatus, House
from app.schemas.booking import BookingCreate
from app.services.booking_service import BookingService


@pytest.fixture(autouse=True)
def disable_external_side_effects(monkeypatch):
    async def noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr(BookingService, "_block_avito_dates", staticmethod(noop))
    monkeypatch.setattr(
        BookingService,
        "_safe_background_sheets_sync",
        classmethod(lambda cls: noop()),
    )


@pytest.fixture
async def booking_db(tmp_path):
    db_path = str(tmp_path / "booking-integrity.db").replace("\\", "/")
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"timeout": 10},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(House(name="Stable House", description="", capacity=4, base_price=5000))
        await session.commit()

    yield session_factory
    await engine.dispose()


def _create_payload(external_id: str, *, house_id: int = 1) -> BookingCreate:
    return BookingCreate(
        house_id=house_id,
        guest_name="Integrity Test",
        guest_phone="+79001234567",
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 12),
        guests_count=2,
        total_price=Decimal("10000"),
        status=BookingStatus.NEW,
        source=BookingSource.YANDEX_TRAVEL,
        external_id=external_id,
    )


@pytest.mark.asyncio
async def test_duplicate_external_id_returns_existing_booking(booking_db):
    async with booking_db() as first_session:
        first = await BookingService.create_booking_result(
            first_session,
            _create_payload("yatr:duplicate-1"),
        )

    async with booking_db() as retry_session:
        retry = await BookingService.create_booking_result(
            retry_session,
            _create_payload("yatr:duplicate-1"),
        )

    assert first.created is True
    assert retry.duplicate is True
    assert retry.booking is not None
    assert first.booking is not None
    assert retry.booking.id == first.booking.id

    async with booking_db() as verify_session:
        count = await verify_session.scalar(select(func.count()).select_from(Booking))
    assert count == 1


@pytest.mark.asyncio
async def test_concurrent_overlapping_create_attempts_serialize(booking_db):
    async def attempt(external_id: str):
        async with booking_db() as session:
            return await BookingService.create_booking_result(
                session,
                _create_payload(external_id),
            )

    outcomes = await asyncio.gather(
        attempt("yatr:concurrent-a"),
        attempt("yatr:concurrent-b"),
    )

    assert sum(outcome.created for outcome in outcomes) == 1
    assert sorted(outcome.reason or "created" for outcome in outcomes) == [
        "created",
        "unavailable",
    ]

    async with booking_db() as verify_session:
        count = await verify_session.scalar(select(func.count()).select_from(Booking))
    assert count == 1


@pytest.mark.asyncio
async def test_unknown_house_is_rejected_at_persistence_boundary(booking_db):
    async with booking_db() as session:
        result = await BookingService.create_booking_result(
            session,
            _create_payload("yatr:unknown-house", house_id=999999),
        )

    assert result.booking is None
    assert result.reason == "unknown_house"

