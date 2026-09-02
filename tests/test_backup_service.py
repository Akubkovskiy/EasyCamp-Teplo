import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from starlette.requests import Request

from app.services import backup_service
from app.services.sqlite_recovery import file_checksum, validate_sqlite_database


def _create_database(path: Path, house_name: str) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE houses (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute(
            """
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY,
                house_id INTEGER NOT NULL REFERENCES houses(id),
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                external_id TEXT
            )
            """
        )
        connection.execute("INSERT INTO houses VALUES (1, ?)", (house_name,))
        connection.commit()


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


def _house_name(path: Path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return str(connection.execute("SELECT name FROM houses WHERE id = 1").fetchone()[0])


def test_drive_backup_uploads_validated_snapshot_not_live_file(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _create_database(live_path, "live")
    capture = {}

    class Request:
        def execute(self):
            return {"id": "uploaded-id", "name": "uploaded.db"}

    class Files:
        def create(self, *, body, media_body, fields):
            snapshot_path = Path(media_body)
            capture["path"] = snapshot_path
            capture["body"] = body
            capture["fields"] = fields
            capture["validation"] = validate_sqlite_database(snapshot_path)
            return Request()

    class Service:
        def files(self):
            return Files()

    monkeypatch.setattr(backup_service.settings, "database_url", _database_url(live_path))
    monkeypatch.setattr(backup_service, "_drive_service", lambda scopes: Service())
    monkeypatch.setattr(
        backup_service,
        "MediaFileUpload",
        lambda path, **kwargs: path,
    )

    result = backup_service._backup_database_to_drive_sync()

    assert result["id"] == "uploaded-id"
    assert capture["path"] != live_path
    assert capture["validation"].sha256 == capture["body"]["appProperties"]["sha256"]
    assert not capture["path"].exists()


def test_drive_restore_uses_explicit_id_checksum_and_atomic_path(tmp_path, monkeypatch):
    candidate = tmp_path / "download-source.db"
    target = tmp_path / "target.db"
    _create_database(candidate, "restored")
    _create_database(target, "original")
    selected_ids = []

    monkeypatch.setattr(backup_service.settings, "database_url", _database_url(target))
    monkeypatch.setattr(backup_service.settings, "restore_from_drive_enabled", True)
    monkeypatch.setattr(backup_service.settings, "restore_maintenance_mode", True)
    monkeypatch.setattr(backup_service.settings, "restore_allow_overwrite", True)
    monkeypatch.setattr(backup_service.settings, "restore_drive_file_id", "chosen-id")
    for setting_name in (
        "enable_auto_sync",
        "sync_on_bot_start",
        "sync_on_user_interaction",
        "enable_yandex_travel_sync",
        "enable_yandex_travel_price_sync",
        "enable_avito_price_sync",
        "enable_auto_discounts",
    ):
        monkeypatch.setattr(backup_service.settings, setting_name, False)

    monkeypatch.setattr(backup_service, "_drive_service", lambda scopes: object())

    def select_backup(service, file_id):
        selected_ids.append(file_id)
        return {
            "id": file_id,
            "name": "easycamp_backup_selected.db",
            "createdTime": "2026-09-02T00:00:00Z",
            "appProperties": {"sha256": file_checksum(candidate)},
        }

    def download(service, file_id, destination):
        destination.write_bytes(candidate.read_bytes())

    monkeypatch.setattr(backup_service, "_selected_drive_backup", select_backup)
    monkeypatch.setattr(backup_service, "_download_drive_file", download)

    result = backup_service._restore_drive_backup_sync()

    assert selected_ids == ["chosen-id"]
    assert _house_name(target) == "restored"
    assert result.rollback_path is not None
    assert _house_name(result.rollback_path) == "original"


@pytest.mark.asyncio
async def test_maintenance_startup_restores_without_initializing_application(monkeypatch):
    import app.database as database
    import app.main as main

    calls = []

    async def fake_restore():
        calls.append("restore")

    async def forbidden_init():
        raise AssertionError("database initialization must stay disabled")

    monkeypatch.setattr(main.settings, "restore_from_drive_enabled", True)
    monkeypatch.setattr(main.settings, "restore_maintenance_mode", True)
    monkeypatch.setattr(backup_service, "restore_drive_backup", fake_restore)
    monkeypatch.setattr(database, "init_db", forbidden_init)

    await main.on_startup()

    assert calls == ["restore"]


@pytest.mark.asyncio
async def test_maintenance_http_guard_blocks_non_health_routes(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main.settings, "restore_maintenance_mode", True)
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/leads",
            "raw_path": b"/api/leads",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "server": ("test", 80),
        }
    )

    async def forbidden_call_next(request):
        raise AssertionError("maintenance request reached application route")

    response = await main.maintenance_mode_guard(request, forbidden_call_next)

    assert response.status_code == 503
