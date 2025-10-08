"""add daily summary time to private bot group binding

Revision ID: 90e3c0b12a65
Revises: cda6e3d9d79c
Create Date: 2025-10-08 10:49:33.089471+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '90e3c0b12a65'
down_revision: Union[str, Sequence[str], None] = 'cda6e3d9d79c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add daily_summary_time column to private_bot_group_binding table
    op.add_column('private_bot_group_binding',
                  sa.Column('daily_summary_time', sa.String(5), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove daily_summary_time column from private_bot_group_binding table
    op.drop_column('private_bot_group_binding', 'daily_summary_time')
