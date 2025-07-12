"""add_shift_configurations_table_with_multiple_times

Revision ID: c30c1ebb4269
Revises: 86dc930a27d1
Create Date: 2025-07-13 05:40:40.275458+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c30c1ebb4269'
down_revision: Union[str, Sequence[str], None] = '86dc930a27d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if shift_configurations table exists and update it if needed
    from sqlalchemy import inspect
    from alembic import context
    
    inspector = inspect(context.get_bind())
    
    if 'shift_configurations' not in inspector.get_table_names():
        # Create shift_configurations table with multiple auto-close times support
        op.create_table(
            'shift_configurations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('chat_id', sa.BigInteger(), nullable=False),
            sa.Column('auto_close_enabled', sa.Boolean(), nullable=False, default=False),
            sa.Column('auto_close_times', sa.Text(), nullable=True),  # JSON array of times
            sa.Column('shift_name_prefix', sa.String(50), nullable=True, default='Shift'),
            sa.Column('reset_numbering_daily', sa.Boolean(), nullable=False, default=True),
            sa.Column('timezone', sa.String(50), nullable=True, default='Asia/Phnom_Penh'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(now())')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(now())')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chat_id')
        )
    else:
        # Table exists, check if it has the correct structure and update if needed
        columns = [col['name'] for col in inspector.get_columns('shift_configurations')]
        
        # Remove old columns if they exist (from previous implementation)
        if 'auto_close_time' in columns:
            op.drop_column('shift_configurations', 'auto_close_time')
        if 'auto_close_after_hours' in columns:
            op.drop_column('shift_configurations', 'auto_close_after_hours')
        
        # Add new auto_close_times column if it doesn't exist
        if 'auto_close_times' not in columns:
            op.add_column('shift_configurations', sa.Column('auto_close_times', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop shift_configurations table
    op.drop_table('shift_configurations')
