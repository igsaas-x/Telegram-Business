"""update unlimited to standard

Revision ID: 2s8arzppm5da
Revises: 48a5b6c7d8e9
Create Date: 2025-07-26 20:48:08.196899+07:00

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2s8arzppm5da'
down_revision: Union[str, Sequence[str], None] = '48a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update UNLIMITED package names to STANDARD."""
    # Step 1: Add STANDARD to the enum (keeping UNLIMITED temporarily)
    op.execute(
        "ALTER TABLE group_package MODIFY COLUMN package ENUM('TRIAL', 'FREE', 'BASIC', 'UNLIMITED', 'STANDARD', 'BUSINESS') NOT NULL DEFAULT 'TRIAL'"
    )
    
    # Step 2: Update all existing UNLIMITED packages to STANDARD
    op.execute(
        "UPDATE group_package SET package = 'STANDARD' WHERE package = 'UNLIMITED'"
    )
    
    # Step 3: Remove UNLIMITED from the enum (now that no data uses it)
    op.execute(
        "ALTER TABLE group_package MODIFY COLUMN package ENUM('TRIAL', 'FREE', 'BASIC', 'STANDARD', 'BUSINESS') NOT NULL DEFAULT 'TRIAL'"
    )


def downgrade() -> None:
    """Downgrade schema - Revert STANDARD package names back to UNLIMITED."""
    # Step 1: Add UNLIMITED back to the enum (keeping STANDARD temporarily)
    op.execute(
        "ALTER TABLE group_package MODIFY COLUMN package ENUM('TRIAL', 'FREE', 'BASIC', 'UNLIMITED', 'STANDARD', 'BUSINESS') NOT NULL DEFAULT 'TRIAL'"
    )
    
    # Step 2: Revert all STANDARD packages back to UNLIMITED
    op.execute(
        "UPDATE group_package SET package = 'UNLIMITED' WHERE package = 'STANDARD'"
    )
    
    # Step 3: Remove STANDARD from the enum (now that no data uses it)
    op.execute(
        "ALTER TABLE group_package MODIFY COLUMN package ENUM('TRIAL', 'FREE', 'BASIC', 'UNLIMITED', 'BUSINESS') NOT NULL DEFAULT 'TRIAL'"
    )