"""add_user_relationship_to_chats

Revision ID: 1fe4de4489fa
Revises: 681f7a4dbcf4
Create Date: 2025-07-08 17:41:34.042314+07:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1fe4de4489fa"
down_revision: Union[str, Sequence[str], None] = "681f7a4dbcf4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chats", sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")))


def downgrade() -> None:
    op.drop_column("chats", "user_id")
