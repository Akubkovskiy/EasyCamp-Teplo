"""Read-only database readiness checks shared by startup and HTTP probes."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.database import engine
from app.models import Booking, House

REQUIRED_TABLE_COLUMNS = {
    House.__tablename__: frozenset(column.name for column in House.__table__.columns),
    Booking.__tablename__: frozenset(column.name for column in Booking.__table__.columns),
}
REQUIRED_TABLES = frozenset(REQUIRED_TABLE_COLUMNS)
REQUIRED_BOOKING_INDEX = "uq_bookings_source_external_id"


@dataclass(frozen=True)
class DatabaseReadiness:
    ready: bool
    reason: str
    missing_tables: tuple[str, ...] = ()
    missing_columns: tuple[str, ...] = ()
    missing_index: str | None = None
    foreign_key_violations: int = 0


class DatabaseNotReadyError(RuntimeError):
    """Startup cannot safely enable booking writers."""


async def check_database_readiness(
    database_engine: AsyncEngine | None = None,
) -> DatabaseReadiness:
    """Check connectivity and the schema required by current booking writers."""

    active_engine = database_engine or engine
    try:
        async with active_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            table_rows = await connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name IN ('houses', 'bookings')"
                )
            )
            tables = {str(row[0]) for row in table_rows}

            missing_columns = []
            for table, required_columns in REQUIRED_TABLE_COLUMNS.items():
                if table not in tables:
                    continue
                column_rows = await connection.execute(text(f'PRAGMA table_info("{table}")'))
                columns = {str(row[1]) for row in column_rows}
                missing_columns.extend(
                    f"{table}.{column}" for column in sorted(required_columns - columns)
                )

            index_rows = await connection.execute(text("PRAGMA index_list('bookings')"))
            booking_index = next(
                (row for row in index_rows if str(row[1]) == REQUIRED_BOOKING_INDEX),
                None,
            )
            index_columns = await connection.execute(
                text(f'PRAGMA index_info("{REQUIRED_BOOKING_INDEX}")')
            )
            booking_index_columns = [str(row[2]) for row in index_columns]
            has_booking_index = bool(
                booking_index
                and booking_index[2] == 1
                and booking_index[4] == 0
                and booking_index_columns == ["source", "external_id"]
            )
            foreign_key_rows = await connection.execute(text("PRAGMA foreign_key_check"))
            foreign_key_violations = len(foreign_key_rows.fetchall())
    except SQLAlchemyError:
        return DatabaseReadiness(ready=False, reason="database_unavailable")

    missing_tables = tuple(sorted(REQUIRED_TABLES - tables))
    if missing_tables:
        return DatabaseReadiness(
            ready=False,
            reason="schema_missing_tables",
            missing_tables=missing_tables,
        )
    if missing_columns:
        return DatabaseReadiness(
            ready=False,
            reason="schema_missing_columns",
            missing_columns=tuple(missing_columns),
        )
    if not has_booking_index:
        return DatabaseReadiness(
            ready=False,
            reason="migration_required",
            missing_index=REQUIRED_BOOKING_INDEX,
        )
    if foreign_key_violations:
        return DatabaseReadiness(
            ready=False,
            reason="referential_integrity_failed",
            foreign_key_violations=foreign_key_violations,
        )
    return DatabaseReadiness(ready=True, reason="ready")


async def assert_database_ready(database_engine: AsyncEngine | None = None) -> None:
    readiness = await check_database_readiness(database_engine)
    if not readiness.ready:
        raise DatabaseNotReadyError(
            "Database readiness gate failed before writers started: "
            f"reason={readiness.reason} "
            f"missing_tables={list(readiness.missing_tables)} "
            f"missing_columns={list(readiness.missing_columns)} "
            f"missing_index={readiness.missing_index} "
            f"foreign_key_violations={readiness.foreign_key_violations}"
        )
