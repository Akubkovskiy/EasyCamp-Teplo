"""add_auth_fields_to_user

Revision ID: 545e7fe519d5
Revises: f93d2f12f708
Create Date: 2026-02-02 20:06:03.324606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '545e7fe519d5'
down_revision: Union[str, Sequence[str], None] = 'f93d2f12f708'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    NOTE: sqlite batch alter previously caused CircularDependencyError on some states.
    We keep this migration idempotent and avoid complex batch reorder.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    cols = {c["name"] for c in insp.get_columns("users")}
    idxs = {i["name"] for i in insp.get_indexes("users")}

    if "username" not in cols:
        op.add_column("users", sa.Column("username", sa.String(), nullable=True))
    if "hashed_password" not in cols:
        op.add_column("users", sa.Column("hashed_password", sa.String(), nullable=True))

    # telegram_id nullable change may require batch mode on sqlite
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("telegram_id", existing_type=sa.INTEGER(), nullable=True)

    if "ix_users_username" not in idxs:
        op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    cols = {c["name"] for c in insp.get_columns("users")}
    idxs = {i["name"] for i in insp.get_indexes("users")}

    if "ix_users_username" in idxs:
        op.drop_index("ix_users_username", table_name="users")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("telegram_id", existing_type=sa.INTEGER(), nullable=False)

    if "hashed_password" in cols:
        op.drop_column("users", "hashed_password")
    if "username" in cols:
        op.drop_column("users", "username")
