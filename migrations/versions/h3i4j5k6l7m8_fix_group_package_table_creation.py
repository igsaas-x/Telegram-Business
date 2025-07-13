"""fix_group_package_table_creation

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2025-07-13 16:15:00.000000+07:00

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h3i4j5k6l7m8"
down_revision: Union[str, Sequence[str], None] = "g2h3i4j5k6l7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists, create if it doesn't
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'group_package' not in inspector.get_table_names():
        # Create the group_package table
        op.create_table(
            "group_package",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("chat_group_id", sa.Integer, nullable=False),
            sa.Column("package", sa.Enum("TRIAL", "BASIC", "UNLIMITED", "BUSINESS", name="servicepackage"), nullable=False, server_default="TRIAL"),
            sa.Column("is_paid", sa.Boolean, default=False),
            sa.Column("package_start_date", sa.DateTime, nullable=True),
            sa.Column("package_end_date", sa.DateTime, nullable=True),
            sa.Column("last_paid_date", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        )

        # Add foreign key constraint
        op.create_foreign_key(
            "fk_group_package_chat_group_id",
            "group_package",
            "chat_group",
            ["chat_group_id"],
            ["id"]
        )
        
        # Add unique constraint on chat_group_id
        op.create_unique_constraint("uq_group_package_chat_group_id", "group_package", ["chat_group_id"])
        
        # Now populate the table for active chats
        trial_start = datetime(2025, 7, 13, 0, 0, 0)
        trial_end = datetime(2025, 7, 20, 23, 59, 59)
        current_time = datetime.now()
        
        # Insert group packages for all active chats
        op.execute(f"""
            INSERT INTO group_package (chat_group_id, package, is_paid, package_start_date, package_end_date, created_at, updated_at)
            SELECT 
                id as chat_group_id,
                'TRIAL' as package,
                false as is_paid,
                '{trial_start.strftime('%Y-%m-%d %H:%M:%S')}' as package_start_date,
                '{trial_end.strftime('%Y-%m-%d %H:%M:%S')}' as package_end_date,
                '{current_time.strftime('%Y-%m-%d %H:%M:%S')}' as created_at,
                '{current_time.strftime('%Y-%m-%d %H:%M:%S')}' as updated_at
            FROM chat_group 
            WHERE is_active = true
            AND id NOT IN (SELECT chat_group_id FROM group_package WHERE chat_group_id IS NOT NULL)
        """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the group_package table if it exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'group_package' in inspector.get_table_names():
        op.drop_table("group_package")