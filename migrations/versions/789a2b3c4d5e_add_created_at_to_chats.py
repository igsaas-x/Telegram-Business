"""add_created_at_to_chats

Revision ID: 789a2b3c4d5e
Revises: 681f7a4dbcf4
Create Date: 2025-07-09 14:30:00.000000+07:00
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "789a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = "03_modify_name_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists before trying to add it
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)  # type: ignore
    columns = [col["name"] for col in inspector.get_columns("chats")]

    if "created_at" not in columns:
        op.add_column(
            "chats",
            sa.Column(
                "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
            ),
        )
        # Set created_at for existing chats to current timestamp
        op.execute("UPDATE chats SET created_at = NOW() WHERE created_at IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns("chats")]

    if "created_at" in columns:
        op.drop_column("chats", "created_at")
