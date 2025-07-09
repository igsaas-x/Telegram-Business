"""Make first_name and last_name nullable and not unique

Revision ID: 03_modify_name_fields
Revises: 02_add_timestamps
Create Date: 2025-07-08 15:39:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '03_modify_name_fields'
down_revision = '02_add_timestamps'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL-compatible approach: directly alter columns to remove unique and make nullable
    conn = op.get_bind()
    
    # Use raw SQL to modify first_name column
    conn.execute(sa.text(
        "ALTER TABLE users MODIFY first_name VARCHAR(50) NULL"
    ))
    
    # Use raw SQL to modify last_name column
    conn.execute(sa.text(
        "ALTER TABLE users MODIFY last_name VARCHAR(50) NULL"
    ))


def downgrade() -> None:
    # Revert columns back to not nullable and unique
    conn = op.get_bind()
    
    # Use raw SQL to revert first_name column
    conn.execute(sa.text(
        "ALTER TABLE users MODIFY first_name VARCHAR(50) NOT NULL UNIQUE"
    ))
    
    # Use raw SQL to revert last_name column
    conn.execute(sa.text(
        "ALTER TABLE users MODIFY last_name VARCHAR(50) NOT NULL UNIQUE"
    ))
