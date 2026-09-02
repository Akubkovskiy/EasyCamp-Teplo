"""add unique external booking identity

Revision ID: c8b1a6f4d2e9
Revises: a1b2c3d4e5f6
Create Date: 2026-09-02 00:00:00

The migration is intentionally non-destructive.  It refuses to add the
constraint when legacy duplicate source/external_id pairs exist so an operator
can reconcile those rows from a backup instead of losing reservation data.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8b1a6f4d2e9"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "uq_bookings_source_external_id"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "bookings" not in inspector.get_table_names():
        raise RuntimeError("bookings table is missing; initialize the database before this migration")

    columns = {column["name"] for column in inspector.get_columns("bookings")}
    required = {"source", "external_id"}
    if not required.issubset(columns):
        missing = ", ".join(sorted(required - columns))
        raise RuntimeError(f"bookings table is missing required columns: {missing}")

    duplicates = bind.execute(
        sa.text(
            """
            SELECT source, external_id, COUNT(*) AS duplicate_count
            FROM bookings
            WHERE external_id IS NOT NULL
            GROUP BY source, external_id
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC, source, external_id
            LIMIT 20
            """
        )
    ).fetchall()
    if duplicates:
        sample = "; ".join(
            f"source={row.source!r} external_id={row.external_id!r} count={row.duplicate_count}"
            for row in duplicates
        )
        raise RuntimeError(
            "Cannot add unique external booking identity: duplicate rows exist. "
            f"Reconcile them from a verified backup first. Sample: {sample}"
        )

    indexes = {index["name"] for index in inspector.get_indexes("bookings")}
    if INDEX_NAME not in indexes:
        op.create_index(
            INDEX_NAME,
            "bookings",
            ["source", "external_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "bookings" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("bookings")}
    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name="bookings")
