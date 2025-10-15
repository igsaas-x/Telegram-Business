"""create_custom_reports_table

Revision ID: cd77f6b28d86
Revises: 90e3c0b12a65
Create Date: 2025-10-15 08:38:51.240047+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cd77f6b28d86'
down_revision: Union[str, Sequence[str], None] = '90e3c0b12a65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create custom_reports table
    op.create_table(
        'custom_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_group_id', sa.Integer(), nullable=False),
        sa.Column('report_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sql_query', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('schedule_time', sa.String(length=5), nullable=True),
        sa.Column('schedule_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chat_group_id'], ['chat_group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_chat_group_id', 'custom_reports', ['chat_group_id'])
    op.create_index('idx_chat_group_id_active', 'custom_reports', ['chat_group_id', 'is_active'])

    # Create unique constraint
    op.create_unique_constraint('unique_group_report_name', 'custom_reports', ['chat_group_id', 'report_name'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_constraint('unique_group_report_name', 'custom_reports', type_='unique')

    # Drop indexes
    op.drop_index('idx_chat_group_id_active', table_name='custom_reports')
    op.drop_index('idx_chat_group_id', table_name='custom_reports')

    # Drop table
    op.drop_table('custom_reports')
