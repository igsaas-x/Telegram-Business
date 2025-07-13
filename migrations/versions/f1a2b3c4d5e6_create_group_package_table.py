"""create_group_package_table

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2025-07-13 11:00:00.000000+07:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the group_package table
    op.create_table(
        "group_package",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("package", sa.Enum("TRIAL", "BASIC", "PRO", "BUSINESS", name="servicepackage"), nullable=False, server_default="TRIAL"),
        sa.Column("is_paid", sa.Boolean, default=False),
        sa.Column("package_start_date", sa.DateTime, nullable=True),
        sa.Column("package_end_date", sa.DateTime, nullable=True),
        sa.Column("last_paid_date", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_group_package_chat_id", 
        "group_package", 
        "chat_group", 
        ["chat_id"], 
        ["chat_id"]
    )
    
    # Add unique constraint on chat_id
    op.create_unique_constraint("uq_group_package_chat_id", "group_package", ["chat_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the group_package table
    op.drop_table("group_package")