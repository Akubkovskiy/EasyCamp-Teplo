import sqlite3
from datetime import date
from contextlib import closing
from pathlib import Path

import pytest
from fastapi import Response
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import health
from app.database import Base
from app.models import Booking, BookingSource, BookingStatus
from app.services import readiness_service
from app.services.readiness_service import DatabaseNotReadyError


def _create_readiness_database(
    path: Path,
    *,
    include_index: bool,
    omitted_column: str | None = None,
) -> None:
    with closing(sqlite3.connect(path)) as connection:
        for table, columns in readiness_service.REQUIRED_TABLE_COLUMNS.items():
            definitions = []
            for column in sorted(columns):
                qualified_name = f"{table}.{column}"
                if qualified_name == omitted_column:
                    continue
                definition = f'"{column}" INTEGER PRIMARY KEY' if column == "id" else f'"{column}" TEXT'
                definitions.append(definition)
            connection.execute(f'CREATE TABLE "{table}" ({", ".join(definitions)})')
        if include_index:
            connection.execute(
                "CREATE UNIQUE INDEX uq_bookings_source_external_id "
                "ON bookings(source, external_id)"
            )
        connection.commit()


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


@pytest.mark.asyncio
async def test_readiness_is_green_for_required_schema(tmp_path, monkeypatch):
    database_path = tmp_path / "ready.db"
    _create_readiness_database(database_path, include_index=True)
    test_engine = create_async_engine(_database_url(database_path))
    monkeypatch.setattr(readiness_service, "engine", test_engine)
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", False)

    try:
        response = Response()
        result = await health.readiness(response)
    finally:
        await test_engine.dispose()

    assert response.status_code == 200
    assert result["status"] == "ready"


@pytest.mark.asyncio
async def test_readiness_rejects_missing_booking_writer_column(tmp_path, monkeypatch):
    database_path = tmp_path / "incomplete-schema.db"
    _create_readiness_database(
        database_path,
        include_index=True,
        omitted_column="bookings.guest_name",
    )
    test_engine = create_async_engine(_database_url(database_path))
    monkeypatch.setattr(readiness_service, "engine", test_engine)
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", False)

    try:
        response = Response()
        result = await health.readiness(response)
        with pytest.raises(DatabaseNotReadyError, match="schema_missing_columns"):
            await readiness_service.assert_database_ready(test_engine)
    finally:
        await test_engine.dispose()

    assert response.status_code == 503
    assert result == {
        "status": "not_ready",
        "reason": "schema_missing_columns",
        "missing_columns": ["bookings.guest_name"],
    }


@pytest.mark.asyncio
async def test_readiness_requires_booking_identity_migration(tmp_path, monkeypatch):
    database_path = tmp_path / "old-schema.db"
    _create_readiness_database(database_path, include_index=False)
    test_engine = create_async_engine(_database_url(database_path))
    monkeypatch.setattr(readiness_service, "engine", test_engine)
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", False)

    try:
        response = Response()
        result = await health.readiness(response)
        with pytest.raises(DatabaseNotReadyError, match="migration_required"):
            await readiness_service.assert_database_ready(test_engine)
    finally:
        await test_engine.dispose()

    assert response.status_code == 503
    assert result == {
        "status": "not_ready",
        "reason": "migration_required",
        "missing_index": "uq_bookings_source_external_id",
    }


@pytest.mark.asyncio
async def test_readiness_rejects_foreign_key_violations(tmp_path, monkeypatch):
    database_path = tmp_path / "orphan.db"
    test_engine = create_async_engine(_database_url(database_path))
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            Booking(
                house_id=999,
                guest_name="Orphan",
                guest_phone="000",
                check_in=date(2026, 9, 10),
                check_out=date(2026, 9, 11),
                guests_count=2,
                status=BookingStatus.CONFIRMED,
                source=BookingSource.DIRECT,
            )
        )
        await session.commit()

    monkeypatch.setattr(readiness_service, "engine", test_engine)
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", False)
    try:
        response = Response()
        result = await health.readiness(response)
        with pytest.raises(DatabaseNotReadyError, match="referential_integrity_failed"):
            await readiness_service.assert_database_ready(test_engine)
    finally:
        await test_engine.dispose()

    assert response.status_code == 503
    assert result == {
        "status": "not_ready",
        "reason": "referential_integrity_failed",
        "foreign_key_violations": 1,
    }


@pytest.mark.asyncio
async def test_readiness_is_disabled_during_restore_maintenance(monkeypatch):
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", True)

    response = Response()
    result = await health.readiness(response)

    assert response.status_code == 503
    assert result == {"status": "not_ready", "reason": "restore_maintenance_mode"}


@pytest.mark.asyncio
async def test_startup_does_not_start_scheduler_when_database_is_not_ready(monkeypatch):
    from app import database, main
    from app.services.scheduler_service import scheduler_service

    calls = []

    async def fake_init_db():
        calls.append("init_db")

    async def fail_readiness():
        calls.append("readiness")
        raise DatabaseNotReadyError("migration_required")

    def forbidden_scheduler_start():
        calls.append("scheduler")

    monkeypatch.setattr(main.settings, "restore_from_drive_enabled", False)
    monkeypatch.setattr(main.settings, "restore_maintenance_mode", False)
    monkeypatch.setattr(database, "init_db", fake_init_db)
    monkeypatch.setattr(readiness_service, "assert_database_ready", fail_readiness)
    monkeypatch.setattr(scheduler_service, "start", forbidden_scheduler_start)

    with pytest.raises(DatabaseNotReadyError, match="migration_required"):
        await main.on_startup()

    assert calls == ["init_db", "readiness"]
