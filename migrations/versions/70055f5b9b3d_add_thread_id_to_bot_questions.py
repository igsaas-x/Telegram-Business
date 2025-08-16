"""add_thread_id_to_bot_questions

Revision ID: 70055f5b9b3d
Revises: j5k6l7m8n9o0
Create Date: 2025-08-16 09:42:25.620140+07:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '70055f5b9b3d'
down_revision: Union[str, Sequence[str], None] = 'j5k6l7m8n9o0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add thread_id column to bot_questions table
    op.add_column('bot_questions', sa.Column('thread_id', sa.Integer(), nullable=False, server_default='0'))
    
    # Remove the server_default after adding the column
    op.alter_column('bot_questions', 'thread_id', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove thread_id column from bot_questions table
    op.drop_column('bot_questions', 'thread_id')
