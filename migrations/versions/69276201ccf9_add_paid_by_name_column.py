"""add_paid_by_name_column

Revision ID: 69276201ccf9
Revises: db7b72db781d
Create Date: 2025-11-17 03:03:07.128132+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '69276201ccf9'
down_revision: Union[str, Sequence[str], None] = 'db7b72db781d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add paid_by_name column to income_balance table
    op.add_column('income_balance', sa.Column('paid_by_name', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove paid_by_name column from income_balance table
    op.drop_column('income_balance', 'paid_by_name')
