"""create_message_table

Revision ID: create_message_table
Revises: 86dc930a27d1
Create Date: 2025-07-12 09:57:17.367308+07:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "create_message_table"
down_revision: Union[str, Sequence[str], None] = "86dc930a27d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Initialize message table"""
    op.create_table(
        "messages",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False
        ),
        sa.Column("chat_id", sa.String(255), nullable=False),
        sa.Column("message_id", sa.String(255), nullable=False),
        sa.Column("original_message", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    """Drop message table"""
    op.drop_table("messages")
