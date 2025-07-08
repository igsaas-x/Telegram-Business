"""add_timestamps_to_income_balance

Revision ID: 02_add_timestamps
Revises: 1fe4de4489fa
Create Date: 2025-07-08 12:01:30.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "02_add_timestamps"
down_revision: Union[str, Sequence[str], None] = "1fe4de4489fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timestamp columns to income_balance table."""
    # Check if columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('income_balance')
    column_names = [c['name'] for c in columns]
    
    # Add created_at column if it doesn't exist
    if 'created_at' not in column_names:
        op.add_column(
            "income_balance",
            sa.Column(
                "created_at", 
                sa.DateTime, 
                nullable=False,
                server_default=sa.func.now()
            )
        )
    
    # Add updated_at column if it doesn't exist
    if 'updated_at' not in column_names:
        op.add_column(
            "income_balance",
            sa.Column(
                "updated_at", 
                sa.DateTime,
                nullable=False,
                server_default=sa.func.now(),
                server_onupdate=sa.func.now()
            )
        )


def downgrade() -> None:
    """Remove timestamp columns from income_balance table."""
    op.drop_column("income_balance", "updated_at")
    op.drop_column("income_balance", "created_at")
