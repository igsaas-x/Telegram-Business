"""add_shift_and_status

Revision ID: 681f7a4dbcf4
Revises: 39f393049227
Create Date: 2025-07-08 10:59:18.834252+07:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "681f7a4dbcf4"
down_revision: Union[str, Sequence[str], None] = "39f393049227"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check what columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Check chats table columns
    chat_columns = inspector.get_columns("chats")
    chat_column_names = [c["name"] for c in chat_columns]

    # Only add is_active if it doesn't exist
    if "is_active" not in chat_column_names:
        op.add_column(
            "chats",
            sa.Column("is_active", sa.Boolean, nullable=True, default=False),
        )

    # Only add enable_shift if it doesn't exist
    if "enable_shift" not in chat_column_names:
        op.add_column(
            "chats",
            sa.Column("enable_shift", sa.Boolean, nullable=True, default=False),
        )

    op.execute("UPDATE chats SET is_active = TRUE WHERE is_active IS NULL")

    # Check income_balance table columns
    income_columns = inspector.get_columns("income_balance")
    income_column_names = [c["name"] for c in income_columns]

    # Only add shift if it doesn't exist
    if "shift" not in income_column_names:
        op.add_column(
            "income_balance",
            sa.Column("shift", sa.Integer, nullable=True, default=1),
        )

    # Only add shift_closed if it doesn't exist
    if "shift_closed" not in income_column_names:
        op.add_column(
            "income_balance",
            sa.Column("shift_closed", sa.Boolean, nullable=True, default=False),
        )

    op.execute(
        "UPDATE income_balance SET shift = 1, shift_closed = FALSE WHERE shift IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
