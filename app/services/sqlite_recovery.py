"""Safe SQLite snapshot and restore primitives.

The functions in this module are deliberately independent from Google Drive and
the async SQLAlchemy engine.  Restore is expected to run in maintenance mode,
before the application opens the database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url

REQUIRED_TABLE_COLUMNS: dict[str, frozenset[str]] = {
    "houses": frozenset({"id", "name"}),
    "bookings": frozenset(
        {
            "id",
            "house_id",
            "check_in",
            "check_out",
            "status",
            "source",
            "external_id",
        }
    ),
}


class SQLiteRecoveryError(RuntimeError):
    """Base class for a rejected snapshot or restore."""


class SQLiteValidationError(SQLiteRecoveryError):
    """The candidate database is corrupt or incompatible."""


class RestoreGateError(SQLiteRecoveryError):
    """A destructive restore precondition was not met."""


@dataclass(frozen=True)
class SQLiteValidation:
    path: Path
    sha256: str
    size_bytes: int
    tables: frozenset[str]
    user_version: int
    alembic_revision: str | None


@dataclass(frozen=True)
class RestoreResult:
    target_path: Path
    installed_sha256: str
    rollback_path: Path | None
    validation: SQLiteValidation


def resolve_sqlite_database_path(database_url: str, *, cwd: Path | None = None) -> Path:
    """Resolve a file-backed SQLite SQLAlchemy URL without string slicing."""

    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise SQLiteRecoveryError(f"Only SQLite databases are supported: {url.drivername}")
    if not url.database or url.database == ":memory:":
        raise SQLiteRecoveryError("A file-backed SQLite database is required")

    path = Path(url.database)
    if not path.is_absolute():
        path = (cwd or Path.cwd()) / path
    return path.resolve()


def file_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Hash a file in bounded chunks."""

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise SQLiteRecoveryError(f"Unsupported checksum algorithm: {algorithm}") from exc

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _read_alembic_revision(connection: sqlite3.Connection, tables: set[str]) -> str | None:
    if "alembic_version" not in tables:
        return None
    row = connection.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
    return str(row[0]) if row else None


def validate_sqlite_database(path: Path) -> SQLiteValidation:
    """Validate integrity, foreign keys, and the minimum EasyCamp schema."""

    path = path.resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise SQLiteValidationError(f"SQLite candidate is missing or empty: {path}")

    try:
        with closing(sqlite3.connect(_readonly_uri(path), uri=True)) as connection:
            integrity_rows = [row[0] for row in connection.execute("PRAGMA integrity_check")]
            if integrity_rows != ["ok"]:
                details = "; ".join(str(row) for row in integrity_rows[:5])
                raise SQLiteValidationError(f"SQLite integrity_check failed: {details}")

            foreign_key_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_rows:
                raise SQLiteValidationError(
                    f"SQLite foreign_key_check found {len(foreign_key_rows)} violation(s)"
                )

            tables = {
                str(row[0])
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            missing_tables = set(REQUIRED_TABLE_COLUMNS) - tables
            if missing_tables:
                raise SQLiteValidationError(
                    f"SQLite schema is missing required table(s): {sorted(missing_tables)}"
                )

            for table, required_columns in REQUIRED_TABLE_COLUMNS.items():
                columns = {
                    str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table}")')
                }
                missing_columns = required_columns - columns
                if missing_columns:
                    raise SQLiteValidationError(
                        f"SQLite table {table!r} is missing column(s): {sorted(missing_columns)}"
                    )

            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            alembic_revision = _read_alembic_revision(connection, tables)
    except SQLiteValidationError:
        raise
    except sqlite3.DatabaseError as exc:
        raise SQLiteValidationError(f"Unable to read SQLite candidate {path}: {exc}") from exc

    return SQLiteValidation(
        path=path,
        sha256=file_checksum(path),
        size_bytes=path.stat().st_size,
        tables=frozenset(tables),
        user_version=user_version,
        alembic_revision=alembic_revision,
    )


def create_sqlite_snapshot(source_path: Path, destination_path: Path) -> SQLiteValidation:
    """Create a transactionally consistent snapshot through SQLite's backup API."""

    source_path = source_path.resolve()
    destination_path = destination_path.resolve()
    if source_path == destination_path:
        raise SQLiteRecoveryError("Snapshot source and destination must differ")
    if not source_path.is_file():
        raise SQLiteRecoveryError(f"SQLite source does not exist: {source_path}")
    if destination_path.exists() and destination_path.stat().st_size:
        raise SQLiteRecoveryError(f"Snapshot destination is not empty: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(_readonly_uri(source_path), uri=True)) as source:
            with closing(sqlite3.connect(destination_path)) as destination:
                source.backup(destination)
    except sqlite3.DatabaseError as exc:
        raise SQLiteRecoveryError(f"SQLite backup API failed for {source_path}: {exc}") from exc

    return validate_sqlite_database(destination_path)


def _owned_temp_path(parent: Path, label: str) -> Path:
    return parent / f".{label}-{uuid4().hex}.db"


def _rollback_path(target_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return target_path.with_name(
        f"{target_path.stem}.pre-restore-{stamp}-{uuid4().hex[:8]}{target_path.suffix}"
    )


def _assert_no_sqlite_sidecars(target_path: Path) -> None:
    sidecars = [
        target_path.with_name(f"{target_path.name}-wal"),
        target_path.with_name(f"{target_path.name}-shm"),
        target_path.with_name(f"{target_path.name}-journal"),
    ]
    present = [str(path) for path in sidecars if path.exists()]
    if present:
        raise RestoreGateError(
            "SQLite sidecar files are present; stop all writers and resolve them before restore: "
            + ", ".join(present)
        )


def apply_sqlite_restore(
    candidate_path: Path,
    target_path: Path,
    *,
    maintenance_mode: bool,
    allow_overwrite: bool,
    expected_checksum: str | None = None,
    checksum_algorithm: str = "sha256",
) -> RestoreResult:
    """Validate, stage, and atomically install a SQLite database.

    The candidate is never moved or removed.  A non-empty target is snapshotted
    first and its rollback file is intentionally retained after success.
    """

    if not maintenance_mode:
        raise RestoreGateError("Restore requires explicit maintenance mode")

    candidate_path = candidate_path.resolve()
    target_path = target_path.resolve()
    if candidate_path == target_path:
        raise RestoreGateError("Restore candidate and target must differ")

    validate_sqlite_database(candidate_path)
    if expected_checksum:
        actual_checksum = file_checksum(candidate_path, checksum_algorithm)
        if actual_checksum.lower() != expected_checksum.lower():
            raise SQLiteValidationError(
                f"{checksum_algorithm} checksum mismatch for restore candidate"
            )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_sqlite_sidecars(target_path)

    target_has_data = target_path.is_file() and target_path.stat().st_size > 0
    if target_has_data and not allow_overwrite:
        raise RestoreGateError(
            "Target database contains data; RESTORE_ALLOW_OVERWRITE=true is required"
        )

    rollback_path: Path | None = None
    if target_has_data:
        rollback_path = _rollback_path(target_path)
        create_sqlite_snapshot(target_path, rollback_path)

    staged_path = _owned_temp_path(target_path.parent, "easycamp-restore-stage")
    swapped = False
    try:
        staged_validation = create_sqlite_snapshot(candidate_path, staged_path)
        os.replace(staged_path, target_path)
        swapped = True

        installed_validation = validate_sqlite_database(target_path)
        if installed_validation.sha256 != staged_validation.sha256:
            raise SQLiteValidationError("Installed database checksum changed during atomic swap")
    except Exception:
        if staged_path.exists():
            staged_path.unlink()

        if swapped and rollback_path is not None and rollback_path.exists():
            rollback_stage = _owned_temp_path(target_path.parent, "easycamp-rollback-stage")
            try:
                rollback_validation = create_sqlite_snapshot(rollback_path, rollback_stage)
                os.replace(rollback_stage, target_path)
                restored_validation = validate_sqlite_database(target_path)
                if restored_validation.sha256 != rollback_validation.sha256:
                    raise SQLiteValidationError(
                        "Rollback database checksum changed during atomic swap"
                    )
            finally:
                if rollback_stage.exists():
                    rollback_stage.unlink()
        elif swapped and target_path.exists():
            failed_path = target_path.with_name(
                f"{target_path.stem}.failed-restore-{uuid4().hex[:8]}{target_path.suffix}"
            )
            os.replace(target_path, failed_path)
        raise

    return RestoreResult(
        target_path=target_path,
        installed_sha256=installed_validation.sha256,
        rollback_path=rollback_path,
        validation=installed_validation,
    )


def _validation_payload(validation: SQLiteValidation) -> dict[str, object]:
    return {
        "path": str(validation.path),
        "sha256": validation.sha256,
        "size_bytes": validation.size_bytes,
        "tables": sorted(validation.tables),
        "user_version": validation.user_version,
        "alembic_revision": validation.alembic_revision,
    }


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe EasyCamp SQLite recovery tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", type=Path)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("source", type=Path)
    snapshot_parser.add_argument("destination", type=Path)

    restore_parser = subparsers.add_parser("restore-local")
    restore_parser.add_argument("candidate", type=Path)
    restore_parser.add_argument("target", type=Path)
    restore_parser.add_argument(
        "--maintenance",
        action="store_true",
        help="required acknowledgement that application writers are stopped",
    )
    restore_parser.add_argument("--allow-overwrite", action="store_true")
    restore_parser.add_argument("--expected-checksum")
    restore_parser.add_argument("--checksum-algorithm", default="sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_cli_parser().parse_args(argv)
    if args.command == "validate":
        payload = _validation_payload(validate_sqlite_database(args.path))
    elif args.command == "snapshot":
        payload = _validation_payload(create_sqlite_snapshot(args.source, args.destination))
    else:
        result = apply_sqlite_restore(
            args.candidate,
            args.target,
            maintenance_mode=args.maintenance,
            allow_overwrite=args.allow_overwrite,
            expected_checksum=args.expected_checksum,
            checksum_algorithm=args.checksum_algorithm,
        )
        payload = {
            "target_path": str(result.target_path),
            "installed_sha256": result.installed_sha256,
            "rollback_path": str(result.rollback_path) if result.rollback_path else None,
            "validation": _validation_payload(result.validation),
        }

    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
