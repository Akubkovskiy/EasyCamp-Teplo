import sqlite3
from contextlib import closing

import pytest

from app.services.house_integrity_service import (
    create_known_orphan_snapshot,
    repair_known_archived_house,
    restore_known_orphan_snapshot,
    validate_known_house4_orphans,
)
from app.services.sqlite_recovery import RestoreGateError, SQLiteValidationError


def _audited_database(path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE houses (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                capacity INTEGER NOT NULL DEFAULT 2,
                base_price INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1
            );
            CREATE TABLE bookings (
                id INTEGER PRIMARY KEY,
                house_id INTEGER NOT NULL REFERENCES houses(id),
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                external_id TEXT
            );
            CREATE TABLE cleaning_tasks (
                id INTEGER PRIMARY KEY,
                booking_id INTEGER NOT NULL REFERENCES bookings(id),
                house_id INTEGER NOT NULL REFERENCES houses(id)
            );
            CREATE TABLE supply_alerts (
                id INTEGER PRIMARY KEY,
                task_id INTEGER REFERENCES cleaning_tasks(id),
                house_id INTEGER REFERENCES houses(id)
            );
            INSERT INTO bookings
                (id, house_id, check_in, check_out, status, source, external_id)
            VALUES
                (31, 4, '2026-03-01', '2026-03-03', 'COMPLETED', 'TELEGRAM', NULL),
                (59, 4, '2026-05-01', '2026-05-02', 'CONFIRMED', 'DIRECT', NULL),
                (75, 4, '2026-06-12', '2026-06-14', 'COMPLETED', 'TELEGRAM', NULL);
            INSERT INTO cleaning_tasks (id, booking_id, house_id)
            VALUES (2, 31, 4), (20, 59, 4), (40, 75, 4);
            INSERT INTO supply_alerts (id, task_id, house_id) VALUES (1, 20, 4);
            """
        )
        connection.commit()


def test_known_orphan_snapshot_and_repair_are_fail_closed(tmp_path):
    database = tmp_path / "easycamp.db"
    snapshot = tmp_path / "easycamp.pre-house4-repair.db"
    _audited_database(database)

    state = validate_known_house4_orphans(database)
    assert state.orphan_rows == {
        "bookings": (31, 59, 75),
        "cleaning_tasks": (2, 20, 40),
        "supply_alerts": (1,),
    }
    snapshot_state = create_known_orphan_snapshot(database, snapshot)

    with pytest.raises(RestoreGateError, match="maintenance mode"):
        repair_known_archived_house(
            database,
            snapshot,
            maintenance_mode=False,
            expected_snapshot_checksum=snapshot_state.sha256,
        )
    with pytest.raises(SQLiteValidationError, match="checksum mismatch"):
        repair_known_archived_house(
            database,
            snapshot,
            maintenance_mode=True,
            expected_snapshot_checksum="0" * 64,
        )

    result = repair_known_archived_house(
        database,
        snapshot,
        maintenance_mode=True,
        expected_snapshot_checksum=snapshot_state.sha256,
    )
    assert result.rollback_snapshot == snapshot
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(
            "SELECT name, is_active FROM houses WHERE id=4"
        ).fetchone() == ("test (archive)", 0)
        assert connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM cleaning_tasks").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM supply_alerts").fetchone()[0] == 1

    rollback = restore_known_orphan_snapshot(
        snapshot,
        database,
        maintenance_mode=True,
        expected_candidate_checksum=snapshot_state.sha256,
        expected_target_checksum=result.installed_sha256,
    )
    assert rollback.forward_snapshot.is_file()
    validate_known_house4_orphans(database)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT 1 FROM houses WHERE id=4").fetchone() is None
        assert len(connection.execute("PRAGMA foreign_key_check").fetchall()) == 7


def test_known_orphan_validator_rejects_drift(tmp_path):
    database = tmp_path / "drift.db"
    _audited_database(database)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            """
            INSERT INTO bookings
                (id, house_id, check_in, check_out, status, source, external_id)
            VALUES (99, 4, '2026-09-01', '2026-09-02', 'NEW', 'DIRECT', NULL)
            """
        )
        connection.commit()

    with pytest.raises(SQLiteValidationError, match="changed since"):
        validate_known_house4_orphans(database)


def test_known_orphan_rollback_rejects_post_repair_writes(tmp_path):
    database = tmp_path / "changed-after-repair.db"
    snapshot = tmp_path / "changed-after-repair.snapshot.db"
    _audited_database(database)
    snapshot_state = create_known_orphan_snapshot(database, snapshot)
    repair = repair_known_archived_house(
        database,
        snapshot,
        maintenance_mode=True,
        expected_snapshot_checksum=snapshot_state.sha256,
    )

    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "UPDATE houses SET description='post-repair change' WHERE id=4"
        )
        connection.commit()

    with pytest.raises(SQLiteValidationError, match="changed after repair"):
        restore_known_orphan_snapshot(
            snapshot,
            database,
            maintenance_mode=True,
            expected_candidate_checksum=snapshot_state.sha256,
            expected_target_checksum=repair.installed_sha256,
        )
