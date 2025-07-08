"""Make first_name and last_name nullable and not unique

Revision ID: 03_modify_name_fields
Revises: 02_add_timestamps_to_income_balance
Create Date: 2025-07-08 15:30:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '03_modify_name_fields'
down_revision = '02_add_timestamps_to_income_balance'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop unique constraints
    op.drop_constraint('users_first_name_key', 'users', type_='unique')
    op.drop_constraint('users_last_name_key', 'users', type_='unique')
    
    # Make columns nullable
    op.alter_column('users', 'first_name',
                    existing_type=sa.String(50),
                    nullable=True)
    op.alter_column('users', 'last_name',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade() -> None:
    # Revert columns back to not nullable
    # Note: This might fail if there are null values in these columns
    op.alter_column('users', 'first_name',
                    existing_type=sa.String(50),
                    nullable=False)
    op.alter_column('users', 'last_name',
                    existing_type=sa.String(50),
                    nullable=False)
    
    # Recreate unique constraints
    op.create_unique_constraint('users_first_name_key', 'users', ['first_name'])
    op.create_unique_constraint('users_last_name_key', 'users', ['last_name'])
