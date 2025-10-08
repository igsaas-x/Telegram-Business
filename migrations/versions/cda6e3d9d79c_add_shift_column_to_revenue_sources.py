"""add_shift_column_to_revenue_sources

Revision ID: cda6e3d9d79c
Revises: a0a16bafe19d
Create Date: 2025-10-05 10:42:16.538473+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cda6e3d9d79c'
down_revision: Union[str, Sequence[str], None] = 'a0a16bafe19d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('revenue_sources', sa.Column('shift', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('revenue_sources', 'shift')
