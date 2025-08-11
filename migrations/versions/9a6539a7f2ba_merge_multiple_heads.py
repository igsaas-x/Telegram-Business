"""merge multiple heads

Revision ID: 9a6539a7f2ba
Revises: i1j2k3l4m5n6, i4j5k6l7m8n9
Create Date: 2025-08-11 04:06:03.052172+07:00

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '9a6539a7f2ba'
down_revision: Union[str, Sequence[str], None] = ('i1j2k3l4m5n6', 'i4j5k6l7m8n9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
