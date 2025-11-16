"""add_category_id_and_nickname_to_sender_configs

Revision ID: db7b72db781d
Revises: 52a6b305ee1e
Create Date: 2025-11-14 14:18:27.122794+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'db7b72db781d'
down_revision: Union[str, Sequence[str], None] = '52a6b305ee1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old unique constraint
    op.drop_constraint('unique_sender_per_chat', 'sender_configs', type_='unique')

    # Add category_id column with foreign key to sender_categories
    op.add_column(
        'sender_configs',
        sa.Column('category_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_sender_category',
        'sender_configs',
        'sender_categories',
        ['category_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add nickname column
    op.add_column(
        'sender_configs',
        sa.Column('nickname', sa.String(length=100), nullable=True)
    )

    # Create new unique constraint with sender_name included
    op.create_unique_constraint(
        'unique_sender_per_chat',
        'sender_configs',
        ['chat_id', 'sender_account_number', 'sender_name']
    )

    # Create index on category_id for faster lookups
    op.create_index(
        'idx_sender_configs_category',
        'sender_configs',
        ['category_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index
    op.drop_index('idx_sender_configs_category', table_name='sender_configs')

    # Drop the new unique constraint
    op.drop_constraint('unique_sender_per_chat', 'sender_configs', type_='unique')

    # Drop foreign key and category_id column
    op.drop_constraint('fk_sender_category', 'sender_configs', type_='foreignkey')
    op.drop_column('sender_configs', 'category_id')

    # Drop nickname column
    op.drop_column('sender_configs', 'nickname')

    # Recreate the old unique constraint
    op.create_unique_constraint(
        'unique_sender_per_chat',
        'sender_configs',
        ['chat_id', 'sender_account_number']
    )
