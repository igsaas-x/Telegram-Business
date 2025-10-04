"""add_revenue_sources_table

Revision ID: a0a16bafe19d
Revises: add_shift_permissions_only
Create Date: 2025-10-05 01:47:27.984963+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a0a16bafe19d'
down_revision: Union[str, Sequence[str], None] = 'add_shift_permissions_only'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create revenue_sources table
    op.create_table(
        'revenue_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('income_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=16), nullable=False, server_default='USD'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['income_id'], ['income_balance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for faster lookups
    op.create_index('ix_revenue_sources_income_id', 'revenue_sources', ['income_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_revenue_sources_income_id', table_name='revenue_sources')
    op.drop_table('revenue_sources')
