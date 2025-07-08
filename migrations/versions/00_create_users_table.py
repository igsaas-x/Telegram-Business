"""create_users_table

Revision ID: 00_create_users
Revises: 681f7a4dbcf4
Create Date: 2025-07-08 11:48:15.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "00_create_users"
down_revision: Union[str, Sequence[str], None] = "681f7a4dbcf4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table."""
    # Check if users table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("username", sa.String(50), unique=True, nullable=False),
            sa.Column("first_name", sa.String(50), nullable=False),
            sa.Column("last_name", sa.String(50), nullable=False),
            sa.Column("identifier", sa.String(50), unique=True, nullable=False),
            sa.Column("phone_number", sa.String(20), unique=True, nullable=True),
            sa.Column("is_paid", sa.Boolean, default=False),
            sa.Column("package", sa.Enum("BASIC", "PRO", "UNLIMITED", name="servicepackage"), 
                     nullable=False, server_default="BASIC"),
            sa.Column("is_active", sa.Boolean, default=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )


def downgrade() -> None:
    """Drop users table."""
    op.drop_table("users")
