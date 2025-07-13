"""rename_chats_to_chat_group

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
Create Date: 2025-07-13 10:00:00.000000+07:00

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename the chats table to chat_group
    op.rename_table("chats", "chat_group")


def downgrade() -> None:
    """Downgrade schema."""
    # Rename the chat_group table back to chats
    op.rename_table("chat_group", "chats")