"""add_paid_by_column_to_income_balance

Revision ID: 153ee7efab5b
Revises: cd77f6b28d86
Create Date: 2025-11-09 03:26:05.240880+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '153ee7efab5b'
down_revision: Union[str, Sequence[str], None] = 'cd77f6b28d86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('income_balance', sa.Column('paid_by', sa.String(10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('income_balance', 'paid_by')
