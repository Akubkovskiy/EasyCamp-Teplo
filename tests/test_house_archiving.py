from datetime import date

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, enable_sqlite_foreign_keys
from app.models import Booking, BookingSource, BookingStatus, House
from app.services.house_service import HouseService


@pytest.mark.asyncio
async def test_house_service_hides_and_soft_deletes_houses(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'houses.db'}")
    enable_sqlite_foreign_keys(engine.sync_engine)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        active = House(name="Active", description="", capacity=4, base_price=5000)
        archived = House(
            name="Archived",
            description="",
            capacity=4,
            base_price=0,
            is_active=False,
        )
        session.add_all([active, archived])
        await session.flush()
        session.add(
            Booking(
                house_id=active.id,
                guest_name="Guest",
                guest_phone="000",
                check_in=date(2026, 9, 10),
                check_out=date(2026, 9, 11),
                guests_count=2,
                status=BookingStatus.CONFIRMED,
                source=BookingSource.DIRECT,
            )
        )
        await session.commit()

        assert [house.name for house in await HouseService.get_all_houses(session)] == [
            "Active"
        ]
        assert await HouseService.get_house_by_id(session, archived.id) is None
        assert (
            await HouseService.get_house_by_id(
                session, archived.id, include_inactive=True
            )
        ).name == "Archived"

        assert await HouseService.delete_house(session, active.id) is True
        assert await HouseService.get_all_houses(session) == []
        retained = await HouseService.get_house_by_id(
            session, active.id, include_inactive=True
        )
        assert retained is not None
        assert retained.is_active is False
        assert (await session.execute(select(Booking))).scalars().one().house_id == active.id
        assert await HouseService.delete_house(session, active.id) is False

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlite_foreign_keys_are_enabled_for_registered_engine(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'fk.db'}")
    enable_sqlite_foreign_keys(engine.sync_engine)
    async with engine.connect() as connection:
        assert await connection.scalar(text("PRAGMA foreign_keys")) == 1
    await engine.dispose()
