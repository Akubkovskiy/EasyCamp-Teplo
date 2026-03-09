"""Add pricing tables (house_prices, house_discounts) and base_price to houses

Revision ID: a1b2c3d4e5f6
Revises: 7a1c9d2e5b44
Create Date: 2026-03-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7a1c9d2e5b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add base_price to houses
    op.add_column('houses', sa.Column('base_price', sa.Integer(), nullable=False, server_default='0'))

    # Create house_prices table (seasonal pricing)
    op.create_table(
        'house_prices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('house_id', sa.Integer(), sa.ForeignKey('houses.id'), nullable=False, index=True),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('price_per_night', sa.Integer(), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create house_discounts table
    op.create_table(
        'house_discounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('house_id', sa.Integer(), sa.ForeignKey('houses.id'), nullable=True, index=True),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('discount_percent', sa.Integer(), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('is_auto', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('house_discounts')
    op.drop_table('house_prices')
    op.drop_column('houses', 'base_price')
