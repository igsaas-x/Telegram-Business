"""add index for income date queries

Revision ID: 1342dc4e5577
Revises: h3i4j5k6l7m8
Create Date: 2025-07-14 08:03:29.753882+07:00

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1342dc4e5577'
down_revision: Union[str, Sequence[str], None] = 'h3i4j5k6l7m8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add composite index for chat_id and date-based queries
    # MySQL syntax for functional index
    op.execute('CREATE INDEX idx_income_chat_date ON income_balance (chat_id, (DATE(income_date)))')
    
    # Add individual index for income_date for better query performance
    op.create_index(
        'idx_income_date', 
        'income_balance', 
        ['income_date']
    )
    
    # Add index for chat_id (if not already exists from FK)
    op.create_index(
        'idx_income_chat_id', 
        'income_balance', 
        ['chat_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP INDEX idx_income_chat_date ON income_balance')
    op.drop_index('idx_income_date', 'income_balance')
    op.drop_index('idx_income_chat_id', 'income_balance')
