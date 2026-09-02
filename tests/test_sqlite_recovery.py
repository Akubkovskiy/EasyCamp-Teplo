import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services import sqlite_recovery
from app.services.backup_service import assert_restore_gate
from app.services.sqlite_recovery import (
    RestoreGateError,
    SQLiteValidationError,
    apply_sqlite_restore,
    create_sqlite_snapshot,
    file_checksum,
    resolve_sqlite_database_path,
    validate_sqlite_database,
)


def _create_easycamp_database(path: Path, *, house_name: str = "Teplo") -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
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
        connection.commit()
        connection.execute("INSERT INTO houses (id, name) VALUES (1, ?)", (house_name,))
        connection.execute(
            """
            INSERT INTO bookings (
                id, house_id, check_in, check_out, status, source, external_id
            ) VALUES (1, 1, '2026-09-01', '2026-09-02', 'confirmed', 'direct', 'test-1')
            """
        )
        connection.commit()


def _house_name(path: Path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return str(connection.execute("SELECT name FROM houses WHERE id = 1").fetchone()[0])


def _restore_settings(**updates) -> Settings:
    values = {
        "telegram_bot_token": "test-token",
        "telegram_chat_id": 1,
        "restore_from_drive_enabled": True,
        "restore_maintenance_mode": True,
        "restore_allow_overwrite": False,
        "restore_drive_file_id": "drive-backup-id",
        "enable_auto_sync": False,
        "sync_on_bot_start": False,
        "sync_on_user_interaction": False,
        "enable_yandex_travel_sync": False,
        "enable_yandex_travel_price_sync": False,
        "enable_avito_price_sync": False,
        "enable_auto_discounts": False,
    }
    values.update(updates)
    return Settings(**values)


def test_resolve_sqlite_database_path_uses_sqlalchemy_url_parser(tmp_path: Path):
    resolved = resolve_sqlite_database_path(
        "sqlite+aiosqlite:///data/easycamp.db",
        cwd=tmp_path,
    )

    assert resolved == (tmp_path / "data" / "easycamp.db").resolve()


def test_snapshot_uses_committed_sqlite_view_while_wal_writer_is_open(tmp_path: Path):
    source = tmp_path / "source.db"
    snapshot = tmp_path / "snapshot.db"
    _create_easycamp_database(source)

    writer = sqlite3.connect(source)
    try:
        writer.execute("PRAGMA journal_mode = WAL")
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE houses SET name = 'uncommitted' WHERE id = 1")

        result = create_sqlite_snapshot(source, snapshot)
    finally:
        writer.rollback()
        writer.close()

    assert result.sha256 == file_checksum(snapshot)
    assert _house_name(snapshot) == "Teplo"


def test_validate_rejects_corrupt_and_incompatible_databases(tmp_path: Path):
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"not sqlite")
    with pytest.raises(SQLiteValidationError, match="Unable to read SQLite"):
        validate_sqlite_database(corrupt)

    incompatible = tmp_path / "incompatible.db"
    with closing(sqlite3.connect(incompatible)) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
        connection.commit()
    with pytest.raises(SQLiteValidationError, match="missing required table"):
        validate_sqlite_database(incompatible)


def test_restore_rejects_checksum_mismatch_without_touching_target(tmp_path: Path):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    _create_easycamp_database(candidate, house_name="candidate")
    _create_easycamp_database(target, house_name="original")

    with pytest.raises(SQLiteValidationError, match="checksum mismatch"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=True,
            allow_overwrite=True,
            expected_checksum="0" * 64,
        )

    assert _house_name(target) == "original"
    assert not list(tmp_path.glob("target.pre-restore-*.db"))


def test_restore_requires_maintenance_and_explicit_overwrite(tmp_path: Path):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    _create_easycamp_database(candidate, house_name="candidate")
    _create_easycamp_database(target, house_name="original")

    with pytest.raises(RestoreGateError, match="maintenance mode"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=False,
            allow_overwrite=True,
        )
    with pytest.raises(RestoreGateError, match="RESTORE_ALLOW_OVERWRITE"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=True,
            allow_overwrite=False,
        )

    assert _house_name(target) == "original"


def test_restore_atomically_swaps_and_retains_valid_rollback(tmp_path: Path):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    _create_easycamp_database(candidate, house_name="candidate")
    _create_easycamp_database(target, house_name="original")

    result = apply_sqlite_restore(
        candidate,
        target,
        maintenance_mode=True,
        allow_overwrite=True,
        expected_checksum=file_checksum(candidate),
    )

    assert _house_name(target) == "candidate"
    assert result.installed_sha256 == file_checksum(target)
    assert result.rollback_path is not None
    assert result.rollback_path.exists()
    assert _house_name(result.rollback_path) == "original"
    assert validate_sqlite_database(result.rollback_path).sha256


def test_restore_refuses_sqlite_sidecars_without_deleting_them(tmp_path: Path):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    sidecar = tmp_path / "target.db-wal"
    _create_easycamp_database(candidate)
    sidecar.write_bytes(b"stale writer evidence")

    with pytest.raises(RestoreGateError, match="sidecar files are present"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=True,
            allow_overwrite=False,
        )

    assert sidecar.read_bytes() == b"stale writer evidence"
    assert not target.exists()


def test_failed_swap_keeps_original_target_and_rollback(tmp_path: Path, monkeypatch):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    _create_easycamp_database(candidate, house_name="candidate")
    _create_easycamp_database(target, house_name="original")

    def fail_replace(source, destination):
        raise PermissionError("simulated target lock")

    monkeypatch.setattr(sqlite_recovery.os, "replace", fail_replace)

    with pytest.raises(PermissionError, match="target lock"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=True,
            allow_overwrite=True,
        )

    assert _house_name(target) == "original"
    rollback_paths = list(tmp_path.glob("target.pre-restore-*.db"))
    assert len(rollback_paths) == 1
    assert _house_name(rollback_paths[0]) == "original"
    assert not list(tmp_path.glob(".easycamp-restore-stage-*.db"))


def test_post_swap_validation_failure_restores_original_target(tmp_path: Path, monkeypatch):
    candidate = tmp_path / "candidate.db"
    target = tmp_path / "target.db"
    _create_easycamp_database(candidate, house_name="candidate")
    _create_easycamp_database(target, house_name="original")
    real_validate = sqlite_recovery.validate_sqlite_database
    validation_calls = 0

    def fail_installed_validation(path):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 4:
            raise SQLiteValidationError("simulated post-swap failure")
        return real_validate(path)

    monkeypatch.setattr(
        sqlite_recovery,
        "validate_sqlite_database",
        fail_installed_validation,
    )

    with pytest.raises(SQLiteValidationError, match="post-swap failure"):
        apply_sqlite_restore(
            candidate,
            target,
            maintenance_mode=True,
            allow_overwrite=True,
        )

    assert _house_name(target) == "original"
    assert validation_calls == 6


def test_restore_gate_requires_all_writer_flags_off():
    assert_restore_gate(_restore_settings())

    with pytest.raises(RestoreGateError, match="RESTORE_FROM_DRIVE_ENABLED"):
        assert_restore_gate(_restore_settings(restore_from_drive_enabled=False))

    with pytest.raises(RestoreGateError, match="ENABLE_AUTO_SYNC"):
        assert_restore_gate(_restore_settings(enable_auto_sync=True))

    with pytest.raises(RestoreGateError, match="RESTORE_DRIVE_FILE_ID"):
        assert_restore_gate(_restore_settings(restore_drive_file_id=""))
