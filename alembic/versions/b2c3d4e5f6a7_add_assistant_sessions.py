"""Add server-side assistant session metadata.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-02

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_sessions",
        sa.Column("session_id_hash", sa.String(length=64), nullable=False),
        sa.Column("actor_telegram_id", sa.Integer(), nullable=False),
        sa.Column("actor_role", sa.String(length=16), nullable=False),
        sa.Column("scopes_json", sa.String(length=2048), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by_telegram_id", sa.Integer(), nullable=True),
        sa.Column("revocation_reason", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("session_id_hash"),
    )
    op.create_index(
        "ix_assistant_sessions_actor_telegram_id",
        "assistant_sessions",
        ["actor_telegram_id"],
    )
    op.create_index(
        "ix_assistant_sessions_issued_at",
        "assistant_sessions",
        ["issued_at"],
    )
    op.create_index(
        "ix_assistant_sessions_expires_at",
        "assistant_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assistant_sessions_expires_at",
        table_name="assistant_sessions",
    )
    op.drop_index(
        "ix_assistant_sessions_issued_at",
        table_name="assistant_sessions",
    )
    op.drop_index(
        "ix_assistant_sessions_actor_telegram_id",
        table_name="assistant_sessions",
    )
    op.drop_table("assistant_sessions")
