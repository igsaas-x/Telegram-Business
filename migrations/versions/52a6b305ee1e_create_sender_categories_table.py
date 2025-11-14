"""create_sender_categories_table

Revision ID: 52a6b305ee1e
Revises: 1259e14b49f7
Create Date: 2025-11-14 14:18:01.298635+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '52a6b305ee1e'
down_revision: Union[str, Sequence[str], None] = '1259e14b49f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sender_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('category_name', sa.String(length=100), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id', 'category_name', name='unique_category_per_chat')
    )

    # Create index for faster sorting by display_order
    op.create_index(
        'idx_sender_categories_chat_order',
        'sender_categories',
        ['chat_id', 'display_order']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_sender_categories_chat_order', table_name='sender_categories')
    op.drop_table('sender_categories')
