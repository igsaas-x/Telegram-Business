"""create_sender_configs_table

Revision ID: 1259e14b49f7
Revises: 153ee7efab5b
Create Date: 2025-11-09 04:53:36.255270+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1259e14b49f7'
down_revision: Union[str, Sequence[str], None] = '153ee7efab5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sender_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('sender_account_number', sa.String(length=3), nullable=False),
        sa.Column('sender_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id', 'sender_account_number', name='unique_sender_per_chat')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sender_configs')
