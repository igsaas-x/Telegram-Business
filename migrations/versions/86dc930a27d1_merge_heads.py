"""merge_heads

Revision ID: 86dc930a27d1
Revises: 6ec307e20b94, cd29b260414a
Create Date: 2025-07-11 09:35:09.556714+07:00

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '86dc930a27d1'
down_revision: Union[str, Sequence[str], None] = ('6ec307e20b94', 'cd29b260414a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
