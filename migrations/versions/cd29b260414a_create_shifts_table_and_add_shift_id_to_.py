"""Create shifts table and add shift_id to income_balance

Revision ID: cd29b260414a
Revises: f046bce03312
Create Date: 2025-07-09 07:41:44.952862+07:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd29b260414a"
down_revision: Union[str, Sequence[str], None] = "f046bce03312"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables exist before creating
    from sqlalchemy import inspect
    from alembic import context

    inspector = inspect(context.get_bind())
    tables = inspector.get_table_names()

    # Create shifts table only if it doesn't exist
    if "shifts" not in tables:
        op.create_table(
            "shifts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("chat_id", sa.String(255), nullable=False),
            sa.Column("shift_date", sa.Date(), nullable=False),
            sa.Column("number", sa.Integer(), nullable=False),
            sa.Column("start_time", sa.DateTime(), nullable=False),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("is_closed", sa.Boolean(), nullable=False, default=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(now())"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("(now())"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Check if income_balance table exists before modifying it
    if "income_balance" in tables:
        # Get existing columns
        columns = inspector.get_columns("income_balance")
        column_names = [c["name"] for c in columns]

        # Add shift_id column to income_balance if it doesn't exist
        if "shift_id" not in column_names:
            op.add_column(
                "income_balance", sa.Column("shift_id", sa.Integer(), nullable=True)
            )

        # Only create foreign key if both tables exist and constraint doesn't exist
        if "shifts" in tables:
            try:
                op.create_foreign_key(
                    "fk_income_balance_shift_id",
                    "income_balance",
                    "shifts",
                    ["shift_id"],
                    ["id"],
                )
            except:
                # Foreign key might already exist
                pass

        # Rename old shift columns for backward compatibility
        if "shift" in column_names and "old_shift" not in column_names:
            op.alter_column(
                "income_balance",
                "shift",
                new_column_name="old_shift",
                existing_type=sa.Integer(),
                existing_nullable=True,
            )

        if "shift_closed" in column_names and "old_shift_closed" not in column_names:
            op.alter_column(
                "income_balance",
                "shift_closed",
                new_column_name="old_shift_closed",
                existing_type=sa.Boolean(),
                existing_nullable=True,
            )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key and shift_id column
    op.drop_constraint(
        "fk_income_balance_shift_id", "income_balance", type_="foreignkey"
    )
    op.drop_column("income_balance", "shift_id")

    # Rename columns back
    op.alter_column("income_balance", "old_shift", new_column_name="shift")
    op.alter_column(
        "income_balance", "old_shift_closed", new_column_name="shift_closed"
    )

    # Drop shifts table
    op.drop_table("shifts")
