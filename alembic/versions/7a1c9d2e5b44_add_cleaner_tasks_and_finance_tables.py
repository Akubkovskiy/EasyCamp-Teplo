"""add cleaner task and finance tables

Revision ID: 7a1c9d2e5b44
Revises: 545e7fe519d5
Create Date: 2026-02-27 16:55:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1c9d2e5b44'
down_revision: Union[str, Sequence[str], None] = '545e7fe519d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cleaning_task_status = sa.Enum(
    'PENDING', 'ACCEPTED', 'DECLINED', 'IN_PROGRESS', 'DONE', 'ESCALATED', 'CANCELLED',
    name='cleaningtaskstatus'
)

supply_alert_status = sa.Enum('NEW', 'IN_PROGRESS', 'RESOLVED', name='supplyalertstatus')

payment_entry_type = sa.Enum('CLEANING_FEE', 'SUPPLY_REIMBURSEMENT', 'ADJUSTMENT', name='cleaningpaymententrytype')
payment_status = sa.Enum('ACCRUED', 'APPROVED', 'PAID', 'CANCELLED', name='paymentstatus')
supply_claim_status = sa.Enum('SUBMITTED', 'APPROVED', 'REJECTED', 'PAID', name='supplyclaimstatus')


def upgrade() -> None:
    op.create_table(
        'cleaning_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('status', cleaning_task_status, nullable=False),
        sa.Column('confirm_deadline_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('decline_reason', sa.String(), nullable=True),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id']),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id', name='uq_cleaning_tasks_booking_id'),
    )
    op.create_index('ix_cleaning_tasks_scheduled_date', 'cleaning_tasks', ['scheduled_date'])
    op.create_index('ix_cleaning_tasks_status', 'cleaning_tasks', ['status'])
    op.create_index('ix_cleaning_tasks_assigned_to_user_id', 'cleaning_tasks', ['assigned_to_user_id'])

    op.create_table(
        'cleaning_task_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_checked', sa.Boolean(), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', 'code', name='uq_cleaning_task_checks_task_code'),
    )
    op.create_index('ix_cleaning_task_checks_task_id', 'cleaning_task_checks', ['task_id'])

    op.create_table(
        'cleaning_task_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('telegram_file_id', sa.String(), nullable=False),
        sa.Column('media_type', sa.String(), nullable=False),
        sa.Column('uploaded_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id']),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cleaning_task_media_task_id', 'cleaning_task_media', ['task_id'])

    op.create_table(
        'supply_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('house_id', sa.Integer(), nullable=True),
        sa.Column('reported_by_user_id', sa.Integer(), nullable=True),
        sa.Column('items_json', sa.String(), nullable=True),
        sa.Column('status', supply_alert_status, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id']),
        sa.ForeignKeyConstraint(['reported_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'cleaning_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('base_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('active_from', sa.Date(), nullable=False),
        sa.Column('active_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cleaning_rates_house_id', 'cleaning_rates', ['house_id'])
    op.create_index('ix_cleaning_rates_is_active', 'cleaning_rates', ['is_active'])

    op.create_table(
        'cleaning_payments_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('cleaner_user_id', sa.Integer(), nullable=False),
        sa.Column('entry_type', payment_entry_type, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('period_key', sa.String(), nullable=False),
        sa.Column('status', payment_status, nullable=False),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cleaner_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cleaning_payments_ledger_cleaner_user_id', 'cleaning_payments_ledger', ['cleaner_user_id'])
    op.create_index('ix_cleaning_payments_ledger_period_key', 'cleaning_payments_ledger', ['period_key'])
    op.create_index('ix_cleaning_payments_ledger_status', 'cleaning_payments_ledger', ['status'])
    op.create_unique_constraint(
        'uq_cleaning_fee_per_task',
        'cleaning_payments_ledger',
        ['task_id', 'entry_type']
    )

    op.create_table(
        'supply_expense_claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('house_id', sa.Integer(), nullable=True),
        sa.Column('cleaner_user_id', sa.Integer(), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('amount_total', sa.Numeric(10, 2), nullable=False),
        sa.Column('items_json', sa.String(), nullable=True),
        sa.Column('receipt_photo_file_id', sa.String(), nullable=False),
        sa.Column('status', supply_claim_status, nullable=False),
        sa.Column('admin_comment', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cleaner_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id']),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_supply_expense_claims_cleaner_user_id', 'supply_expense_claims', ['cleaner_user_id'])
    op.create_index('ix_supply_expense_claims_task_id', 'supply_expense_claims', ['task_id'])
    op.create_index('ix_supply_expense_claims_status', 'supply_expense_claims', ['status'])


def downgrade() -> None:
    op.drop_index('ix_supply_expense_claims_status', table_name='supply_expense_claims')
    op.drop_index('ix_supply_expense_claims_task_id', table_name='supply_expense_claims')
    op.drop_index('ix_supply_expense_claims_cleaner_user_id', table_name='supply_expense_claims')
    op.drop_table('supply_expense_claims')

    op.drop_constraint('uq_cleaning_fee_per_task', 'cleaning_payments_ledger', type_='unique')
    op.drop_index('ix_cleaning_payments_ledger_status', table_name='cleaning_payments_ledger')
    op.drop_index('ix_cleaning_payments_ledger_period_key', table_name='cleaning_payments_ledger')
    op.drop_index('ix_cleaning_payments_ledger_cleaner_user_id', table_name='cleaning_payments_ledger')
    op.drop_table('cleaning_payments_ledger')

    op.drop_index('ix_cleaning_rates_is_active', table_name='cleaning_rates')
    op.drop_index('ix_cleaning_rates_house_id', table_name='cleaning_rates')
    op.drop_table('cleaning_rates')

    op.drop_table('supply_alerts')

    op.drop_index('ix_cleaning_task_media_task_id', table_name='cleaning_task_media')
    op.drop_table('cleaning_task_media')

    op.drop_index('ix_cleaning_task_checks_task_id', table_name='cleaning_task_checks')
    op.drop_table('cleaning_task_checks')

    op.drop_index('ix_cleaning_tasks_assigned_to_user_id', table_name='cleaning_tasks')
    op.drop_index('ix_cleaning_tasks_status', table_name='cleaning_tasks')
    op.drop_index('ix_cleaning_tasks_scheduled_date', table_name='cleaning_tasks')
    op.drop_table('cleaning_tasks')

    supply_claim_status.drop(op.get_bind(), checkfirst=True)
    payment_status.drop(op.get_bind(), checkfirst=True)
    payment_entry_type.drop(op.get_bind(), checkfirst=True)
    supply_alert_status.drop(op.get_bind(), checkfirst=True)
    cleaning_task_status.drop(op.get_bind(), checkfirst=True)
