"""add_user_relationship_to_chats

Revision ID: 1fe4de4489fa
Revises: 00_create_users
Create Date: 2025-07-08 17:41:34.042314+07:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1fe4de4489fa"
down_revision: Union[str, Sequence[str], None] = "00_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('chats')
    column_names = [c['name'] for c in columns]
    
    # Only add the column if it doesn't exist
    if 'user_id' not in column_names:
        op.add_column("chats", sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")))


def downgrade() -> None:
    op.drop_column("chats", "user_id")
