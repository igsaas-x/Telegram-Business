"""populate_group_packages_for_active_chats

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2025-07-13 12:00:00.000000+07:00

"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create group packages for all active chat groups with TRIAL package
    # Trial period from 2025-07-13 to 2025-07-20
    
    trial_start = datetime(2025, 7, 13, 0, 0, 0)
    trial_end = datetime(2025, 7, 20, 23, 59, 59)
    current_time = datetime.now()
    
    # Insert group packages for all active chats
    op.execute(f"""
        INSERT INTO group_package (chat_id, package, is_paid, package_start_date, package_end_date, created_at, updated_at)
        SELECT 
            chat_id,
            'TRIAL' as package,
            false as is_paid,
            '{trial_start.strftime('%Y-%m-%d %H:%M:%S')}' as package_start_date,
            '{trial_end.strftime('%Y-%m-%d %H:%M:%S')}' as package_end_date,
            '{current_time.strftime('%Y-%m-%d %H:%M:%S')}' as created_at,
            '{current_time.strftime('%Y-%m-%d %H:%M:%S')}' as updated_at
        FROM chat_group 
        WHERE is_active = true
        AND chat_id NOT IN (SELECT chat_id FROM group_package)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove all TRIAL packages that were created for existing active chats
    trial_start = datetime(2025, 7, 13, 0, 0, 0)
    trial_end = datetime(2025, 7, 20, 23, 59, 59)
    
    op.execute(f"""
        DELETE FROM group_package 
        WHERE package = 'TRIAL' 
        AND package_start_date = '{trial_start.strftime('%Y-%m-%d %H:%M:%S')}'
        AND package_end_date = '{trial_end.strftime('%Y-%m-%d %H:%M:%S')}'
    """)