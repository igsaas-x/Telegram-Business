"""make_trx_id_nullable

Revision ID: 6ec307e20b94
Revises: 789a2b3c4d5e
Create Date: 2025-07-10 10:36:33.303113+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6ec307e20b94'
down_revision: Union[str, Sequence[str], None] = '789a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make trx_id column nullable
    op.alter_column('income_balance', 'trx_id',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make trx_id column non-nullable again (this might fail if there are NULL values)
    op.alter_column('income_balance', 'trx_id',
                    existing_type=sa.String(50),
                    nullable=False)
