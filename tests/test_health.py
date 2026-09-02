import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi import Response
from sqlalchemy.ext.asyncio import create_async_engine

from app.api import health
from app.services import readiness_service
from app.services.readiness_service import DatabaseNotReadyError


def _create_readiness_database(path: Path, *, include_index: bool) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE houses (id INTEGER PRIMARY KEY)")
        connection.execute(
            """
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                external_id TEXT
            )
            """
        )
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
async def test_readiness_is_disabled_during_restore_maintenance(monkeypatch):
    monkeypatch.setattr(health.settings, "restore_maintenance_mode", True)

    response = Response()
    result = await health.readiness(response)

    assert response.status_code == 503
    assert result == {"status": "not_ready", "reason": "restore_maintenance_mode"}


@pytest.mark.asyncio
async def test_startup_does_not_start_scheduler_when_database_is_not_ready(monkeypatch):
    import app.database as database
    import app.main as main
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
