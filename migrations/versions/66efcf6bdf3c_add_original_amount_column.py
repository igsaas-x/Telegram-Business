from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


revision: str = '66efcf6bdf3c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('income_balance',
        sa.Column('original_amount', sa.Float(), nullable=True)
    )
    op.execute(text("UPDATE income_balance SET original_amount = amount"))
    op.alter_column('income_balance', 'original_amount',
                    existing_type=sa.Float(),
                    nullable=False)


def downgrade() -> None:
    op.drop_column('income_balance', 'original_amount')