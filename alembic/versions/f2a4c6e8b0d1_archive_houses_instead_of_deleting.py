"""archive houses instead of deleting them

Revision ID: f2a4c6e8b0d1
Revises: c8b1a6f4d2e9
Create Date: 2026-09-03 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f2a4c6e8b0d1"
down_revision: str | Sequence[str] | None = "c8b1a6f4d2e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "ix_houses_is_active"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "houses" not in inspector.get_table_names():
        raise RuntimeError("houses table is missing; initialize the database first")

    columns = {column["name"] for column in inspector.get_columns("houses")}
    if "is_active" not in columns:
        op.add_column(
            "houses",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
        )

    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("houses")}
    if INDEX_NAME not in indexes:
        op.create_index(INDEX_NAME, "houses", ["is_active"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "houses" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("houses")}
    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name="houses")

    columns = {column["name"] for column in inspector.get_columns("houses")}
    if "is_active" in columns:
        with op.batch_alter_table("houses") as batch_op:
            batch_op.drop_column("is_active")
