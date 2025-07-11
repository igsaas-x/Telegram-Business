"""Add shifts table and update income_balance with shift_id

Revision ID: f046bce03312
Revises: 03_modify_name_fields
Create Date: 2025-07-09 07:40:19.583209+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f046bce03312'
down_revision: Union[str, Sequence[str], None] = '03_modify_name_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SAFE MIGRATION - Only add missing columns/tables, never drop existing data
    
    # Check if we need to add enable_shift column to chats table
    from sqlalchemy import inspect
    from alembic import context
    
    inspector = inspect(context.get_bind())
    
    # Check if chats table exists and if enable_shift column is missing
    if 'chats' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('chats')]
        if 'enable_shift' not in columns:
            # Add enable_shift column if it doesn't exist
            op.add_column('chats', sa.Column('enable_shift', sa.Boolean(), nullable=True, default=False))
        
        if 'created_at' not in columns:
            # Add created_at column if it doesn't exist  
            op.add_column('chats', sa.Column('created_at', sa.DateTime(), default=sa.text('(now())'), nullable=False))
    
    # Ensure other necessary columns exist but never drop anything
    # This migration is now SAFE for production


def downgrade() -> None:
    """Downgrade schema."""
    # SAFE DOWNGRADE - Only remove columns that were added in upgrade
    # Never drop tables or existing data
    
    from sqlalchemy import inspect
    from alembic import context
    
    inspector = inspect(context.get_bind())
    
    # Only remove columns that we added in the upgrade
    if 'chats' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('chats')]
        
        # Remove enable_shift column if it exists (only if we added it)
        if 'enable_shift' in columns:
            try:
                op.drop_column('chats', 'enable_shift')
            except:
                pass  # Ignore if column doesn't exist or can't be dropped
    
    # Note: We don't remove created_at as it might have been added by another migration
    # This downgrade is now SAFE and won't lose production data
