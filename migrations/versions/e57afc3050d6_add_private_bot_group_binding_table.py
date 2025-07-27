"""add_private_bot_group_binding_table

Revision ID: e57afc3050d6
Revises: 2s8arzppm5da
Create Date: 2025-07-27 14:42:11.504985+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e57afc3050d6'
down_revision: Union[str, Sequence[str], None] = '2s8arzppm5da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create private_bot_group_binding table
    op.create_table('private_bot_group_binding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('private_chat_id', sa.BigInteger(), nullable=False),
        sa.Column('bound_group_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bound_group_id'], ['chat_group.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop private_bot_group_binding table
    op.drop_table('private_bot_group_binding')
