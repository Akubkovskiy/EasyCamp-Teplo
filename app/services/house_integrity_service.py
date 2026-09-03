"""One-time, fail-closed repair for the known archived house-4 graph.

This module is intentionally specific.  It will not repair arbitrary foreign
key violations and it never deletes or repoints booking history.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.services.sqlite_recovery import (
    RestoreGateError,
    SQLiteRecoveryError,
    SQLiteValidation,
    SQLiteValidationError,
    _assert_no_sqlite_sidecars,
    create_sqlite_snapshot,
    file_checksum,
    validate_sqlite_database,
)

ARCHIVED_HOUSE_ID = 4
ARCHIVED_HOUSE_NAME = "test (archive)"
EXPECTED_ORPHAN_ROWS: dict[str, frozenset[int]] = {
    "bookings": frozenset({31, 59, 75}),
    "cleaning_tasks": frozenset({2, 20, 40}),
    "supply_alerts": frozenset({1}),
}


@dataclass(frozen=True)
class KnownOrphanState:
    path: Path
    sha256: str
    size_bytes: int
    orphan_rows: dict[str, tuple[int, ...]]


@dataclass(frozen=True)
class ArchivedHouseRepair:
    target_path: Path
    rollback_snapshot: Path
    rollback_sha256: str
    installed_sha256: str


@dataclass(frozen=True)
class KnownOrphanRestore:
    target_path: Path
    restored_sha256: str
    forward_snapshot: Path
    forward_snapshot_sha256: str


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _basic_integrity_check(connection: sqlite3.Connection, path: Path) -> None:
    rows = [str(row[0]) for row in connection.execute("PRAGMA integrity_check")]
    if rows != ["ok"]:
        raise SQLiteValidationError(
            f"SQLite integrity_check failed for {path}: {'; '.join(rows[:5])}"
        )


def validate_known_house4_orphans(path: Path) -> KnownOrphanState:
    """Accept only the audited seven house-4 violations and no others."""

    path = path.resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise SQLiteValidationError(f"SQLite database is missing or empty: {path}")

    try:
        with closing(sqlite3.connect(_readonly_uri(path), uri=True)) as connection:
            _basic_integrity_check(connection, path)
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            missing = (set(EXPECTED_ORPHAN_ROWS) | {"houses"}) - tables
            if missing:
                raise SQLiteValidationError(
                    f"Known orphan repair schema is missing tables: {sorted(missing)}"
                )

            if connection.execute(
                "SELECT 1 FROM houses WHERE id = ?", (ARCHIVED_HOUSE_ID,)
            ).fetchone():
                raise SQLiteValidationError(
                    f"houses.id={ARCHIVED_HOUSE_ID} already exists; repair refused"
                )

            actual: dict[str, set[int]] = {
                table: set() for table in EXPECTED_ORPHAN_ROWS
            }
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            for table, rowid, parent, _fkid in violations:
                table = str(table)
                if parent != "houses" or table not in EXPECTED_ORPHAN_ROWS:
                    raise SQLiteValidationError(
                        "Unexpected foreign-key violation outside the audited house-4 graph"
                    )
                row = connection.execute(
                    f'SELECT id, house_id FROM "{table}" WHERE rowid = ?',
                    (rowid,),
                ).fetchone()
                if not row or int(row[0]) != int(rowid) or int(row[1]) != ARCHIVED_HOUSE_ID:
                    raise SQLiteValidationError(
                        "Foreign-key violation does not match the audited house-4 graph"
                    )
                actual[table].add(int(row[0]))

            if actual != {
                table: set(row_ids) for table, row_ids in EXPECTED_ORPHAN_ROWS.items()
            }:
                raise SQLiteValidationError(
                    "House-4 orphan rows changed since the read-only audit: "
                    + repr({table: sorted(rows) for table, rows in actual.items()})
                )
    except SQLiteValidationError:
        raise
    except sqlite3.DatabaseError as exc:
        raise SQLiteValidationError(f"Unable to inspect {path}: {exc}") from exc

    return KnownOrphanState(
        path=path,
        sha256=file_checksum(path),
        size_bytes=path.stat().st_size,
        orphan_rows={table: tuple(sorted(rows)) for table, rows in actual.items()},
    )


def create_known_orphan_snapshot(
    source_path: Path, destination_path: Path
) -> KnownOrphanState:
    """Create an online rollback snapshot of exactly the audited bad state."""

    source_path = source_path.resolve()
    destination_path = destination_path.resolve()
    validate_known_house4_orphans(source_path)
    if source_path == destination_path:
        raise SQLiteRecoveryError("Snapshot source and destination must differ")
    if destination_path.exists() and destination_path.stat().st_size:
        raise SQLiteRecoveryError(f"Snapshot destination is not empty: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with (
            closing(sqlite3.connect(_readonly_uri(source_path), uri=True)) as source,
            closing(sqlite3.connect(destination_path)) as destination,
        ):
            source.backup(destination)
    except sqlite3.DatabaseError as exc:
        raise SQLiteRecoveryError(
            f"SQLite forensic snapshot failed for {source_path}: {exc}"
        ) from exc

    return validate_known_house4_orphans(destination_path)


def repair_known_archived_house(
    target_path: Path,
    rollback_snapshot: Path,
    *,
    maintenance_mode: bool,
    expected_snapshot_checksum: str,
) -> ArchivedHouseRepair:
    """Restore the inactive parent row only after validating the rollback file."""

    if not maintenance_mode:
        raise RestoreGateError("Archived-house repair requires explicit maintenance mode")
    if not expected_snapshot_checksum:
        raise RestoreGateError("A recorded rollback snapshot checksum is required")

    target_path = target_path.resolve()
    rollback_snapshot = rollback_snapshot.resolve()
    snapshot_state = validate_known_house4_orphans(rollback_snapshot)
    if snapshot_state.sha256.lower() != expected_snapshot_checksum.lower():
        raise SQLiteValidationError("Rollback snapshot checksum mismatch")

    _assert_no_sqlite_sidecars(target_path)
    validate_known_house4_orphans(target_path)

    connection = sqlite3.connect(target_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info('houses')")
        }
        if "is_active" not in columns:
            raise SQLiteValidationError(
                "houses.is_active migration must be applied before the repair"
            )

        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            INSERT INTO houses (
                id, name, description, capacity, base_price, is_active
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ARCHIVED_HOUSE_ID,
                ARCHIVED_HOUSE_NAME,
                "Archived legacy object restored for referential integrity",
                5,
                0,
                False,
            ),
        )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise SQLiteValidationError(
                f"Repair left {len(violations)} foreign-key violation(s)"
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    validation: SQLiteValidation = validate_sqlite_database(target_path)
    return ArchivedHouseRepair(
        target_path=target_path,
        rollback_snapshot=rollback_snapshot,
        rollback_sha256=snapshot_state.sha256,
        installed_sha256=validation.sha256,
    )


def restore_known_orphan_snapshot(
    candidate_path: Path,
    target_path: Path,
    *,
    maintenance_mode: bool,
    expected_candidate_checksum: str,
    expected_target_checksum: str,
) -> KnownOrphanRestore:
    """Atomically restore the audited pre-repair state for full rollback."""

    if not maintenance_mode:
        raise RestoreGateError("Known-orphan rollback requires explicit maintenance mode")
    if not expected_candidate_checksum:
        raise RestoreGateError("A recorded rollback candidate checksum is required")
    if not expected_target_checksum:
        raise RestoreGateError("The recorded repaired-database checksum is required")

    candidate_path = candidate_path.resolve()
    target_path = target_path.resolve()
    if candidate_path == target_path:
        raise RestoreGateError("Rollback candidate and target must differ")

    candidate_state = validate_known_house4_orphans(candidate_path)
    if candidate_state.sha256.lower() != expected_candidate_checksum.lower():
        raise SQLiteValidationError("Rollback candidate checksum mismatch")

    _assert_no_sqlite_sidecars(target_path)
    target_validation = validate_sqlite_database(target_path)
    if target_validation.sha256.lower() != expected_target_checksum.lower():
        raise SQLiteValidationError(
            "Target database changed after repair; automatic rollback refused"
        )

    forward_snapshot = target_path.with_name(
        f"{target_path.stem}.pre-house4-rollback-{uuid4().hex[:8]}{target_path.suffix}"
    )
    forward_validation = create_sqlite_snapshot(target_path, forward_snapshot)
    staged_path = target_path.with_name(
        f".{target_path.stem}.house4-rollback-stage-{uuid4().hex}.db"
    )
    swapped = False
    try:
        with (
            closing(sqlite3.connect(_readonly_uri(candidate_path), uri=True)) as source,
            closing(sqlite3.connect(staged_path)) as destination,
        ):
            source.backup(destination)
        staged_state = validate_known_house4_orphans(staged_path)
        os.replace(staged_path, target_path)
        swapped = True
        installed_state = validate_known_house4_orphans(target_path)
        if installed_state.sha256 != staged_state.sha256:
            raise SQLiteValidationError("Installed rollback checksum changed during atomic swap")
    except Exception:
        if staged_path.exists():
            staged_path.unlink()
        if swapped:
            recovery_stage = target_path.with_name(
                f".{target_path.stem}.house4-forward-stage-{uuid4().hex}.db"
            )
            try:
                create_sqlite_snapshot(forward_snapshot, recovery_stage)
                os.replace(recovery_stage, target_path)
                validate_sqlite_database(target_path)
            finally:
                if recovery_stage.exists():
                    recovery_stage.unlink()
        raise

    return KnownOrphanRestore(
        target_path=target_path,
        restored_sha256=installed_state.sha256,
        forward_snapshot=forward_snapshot,
        forward_snapshot_sha256=forward_validation.sha256,
    )


def _payload(
    state: KnownOrphanState | ArchivedHouseRepair | KnownOrphanRestore,
) -> dict[str, object]:
    if isinstance(state, KnownOrphanState):
        return {
            "path": str(state.path),
            "sha256": state.sha256,
            "size_bytes": state.size_bytes,
            "orphan_rows": state.orphan_rows,
        }
    if isinstance(state, ArchivedHouseRepair):
        return {
            "target_path": str(state.target_path),
            "rollback_snapshot": str(state.rollback_snapshot),
            "rollback_sha256": state.rollback_sha256,
            "installed_sha256": state.installed_sha256,
            "archived_house_id": ARCHIVED_HOUSE_ID,
        }
    return {
        "target_path": str(state.target_path),
        "restored_sha256": state.restored_sha256,
        "forward_snapshot": str(state.forward_snapshot),
        "forward_snapshot_sha256": state.forward_snapshot_sha256,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Known EasyCamp house integrity repair")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-known-house4")
    validate.add_argument("path", type=Path)

    snapshot = subparsers.add_parser("snapshot-known-house4")
    snapshot.add_argument("source", type=Path)
    snapshot.add_argument("destination", type=Path)

    repair = subparsers.add_parser("repair-known-house4")
    repair.add_argument("target", type=Path)
    repair.add_argument("rollback_snapshot", type=Path)
    repair.add_argument("--maintenance", action="store_true")
    repair.add_argument("--expected-snapshot-checksum", required=True)

    rollback = subparsers.add_parser("restore-known-house4-snapshot")
    rollback.add_argument("candidate", type=Path)
    rollback.add_argument("target", type=Path)
    rollback.add_argument("--maintenance", action="store_true")
    rollback.add_argument("--expected-candidate-checksum", required=True)
    rollback.add_argument("--expected-target-checksum", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "validate-known-house4":
        result = validate_known_house4_orphans(args.path)
    elif args.command == "snapshot-known-house4":
        result = create_known_orphan_snapshot(args.source, args.destination)
    elif args.command == "repair-known-house4":
        result = repair_known_archived_house(
            args.target,
            args.rollback_snapshot,
            maintenance_mode=args.maintenance,
            expected_snapshot_checksum=args.expected_snapshot_checksum,
        )
    else:
        result = restore_known_orphan_snapshot(
            args.candidate,
            args.target,
            maintenance_mode=args.maintenance,
            expected_candidate_checksum=args.expected_candidate_checksum,
            expected_target_checksum=args.expected_target_checksum,
        )
    print(json.dumps(_payload(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
