"""add_created_at_and_updated_at_to_bot_questions

Revision ID: created_updated_to_bot_questions
Revises: 1342dc4e5577
Create Date: 2024-07-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "created_updated_to_bot_questions"
down_revision = "1342dc4e5577"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("bot_questions")]

    if "created_at" not in columns:
        op.add_column(
            "bot_questions",
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.execute(
            "UPDATE bot_questions SET created_at = NOW() WHERE created_at IS NULL"
        )

    if "updated_at" not in columns:
        op.add_column(
            "bot_questions",
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            ),
        )
        op.execute(
            "UPDATE bot_questions SET updated_at = NOW() WHERE updated_at IS NULL"
        )


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("bot_questions")]

    if "created_at" in columns:
        op.drop_column("bot_questions", "created_at")
    if "updated_at" in columns:
        op.drop_column("bot_questions", "updated_at")
