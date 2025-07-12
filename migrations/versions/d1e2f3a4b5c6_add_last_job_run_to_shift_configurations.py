"""add_last_job_run_to_shift_configurations

Revision ID: d1e2f3a4b5c6
Revises: c30c1ebb4269
Create Date: 2025-07-12 16:10:00.000000+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c30c1ebb4269'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add last_job_run column to shift_configurations table
    from sqlalchemy import inspect
    from alembic import context
    
    inspector = inspect(context.get_bind())
    
    if 'shift_configurations' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('shift_configurations')]
        
        # Add last_job_run column if it doesn't exist
        if 'last_job_run' not in columns:
            op.add_column('shift_configurations', sa.Column('last_job_run', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove last_job_run column
    op.drop_column('shift_configurations', 'last_job_run')