"""Yandex Travel ingestion must use the hardened booking boundary."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Booking, BookingSource, BookingStatus, House
from app.services.booking_service import BookingService
from app.services.yandex_travel_sync_service import process_yatr_order
from app.yandex_travel.schemas import YaTrGuest, YaTrOrder


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
async def yandex_db(tmp_path):
    db_path = str(tmp_path / "yandex-integrity.db").replace("\\", "/")
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"timeout": 10},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(House(name="Yandex House", description="", capacity=4, base_price=5000))
        await session.commit()

    yield session_factory
    await engine.dispose()


def _order(order_id: str = "order-1") -> YaTrOrder:
    return YaTrOrder(
        order_id=order_id,
        hotel_id="hotel-1",
        room_id="room-1",
        check_in=date(2026, 11, 10),
        check_out=date(2026, 11, 12),
        guests_count=2,
        guest=YaTrGuest(name="Yandex Guest", phone="+79001234567"),
        total_price=10000,
        status="confirmed",
    )


@pytest.mark.asyncio
async def test_yandex_missing_house_mapping_is_rejected(yandex_db):
    async with yandex_db() as session:
        booking = await process_yatr_order(session, _order(), {})
        count = await session.scalar(select(func.count()).select_from(Booking))

    assert booking is None
    assert count == 0


@pytest.mark.asyncio
async def test_yandex_mapping_to_unknown_house_is_rejected(yandex_db):
    async with yandex_db() as session:
        booking = await process_yatr_order(
            session,
            _order("order-unknown-house"),
            {"hotel-1/room-1": 999999},
        )
        count = await session.scalar(select(func.count()).select_from(Booking))

    assert booking is None
    assert count == 0


@pytest.mark.asyncio
async def test_yandex_overlapping_order_is_rejected(yandex_db):
    async with yandex_db() as session:
        session.add(
            Booking(
                house_id=1,
                guest_name="Existing Guest",
                guest_phone="+79001111111",
                check_in=date(2026, 11, 9),
                check_out=date(2026, 11, 11),
                guests_count=2,
                total_price=Decimal("9000"),
                advance_amount=Decimal("0"),
                commission=Decimal("0"),
                prepayment_owner=Decimal("0"),
                status=BookingStatus.CONFIRMED,
                source=BookingSource.DIRECT,
            )
        )
        await session.commit()

        booking = await process_yatr_order(
            session,
            _order("order-overlap"),
            {"hotel-1/room-1": 1},
        )
        count = await session.scalar(select(func.count()).select_from(Booking))

    assert booking is None
    assert count == 1
