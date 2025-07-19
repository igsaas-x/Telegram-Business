"""create initial tables

Revision ID: create_initial_table
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from common.enums import ServicePackage

# revision identifiers, used by Alembic.
revision = "create_initial_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chats table (will be renamed to chat_group in later migration)
    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.BigInteger(), unique=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create basic income_balance table
    # Additional columns will be added by later migrations
    op.create_table(
        "income_balance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("income_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create bot_questions table
    op.create_table(
        "bot_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("question_type", sa.String(32), nullable=False),
        sa.Column("is_replied", sa.Boolean(), default=False),
        sa.Column("context_data", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation to handle dependencies
    op.drop_table("bot_questions")
    op.drop_table("income_balance")
    op.drop_table("chats")
    op.drop_table("users")
