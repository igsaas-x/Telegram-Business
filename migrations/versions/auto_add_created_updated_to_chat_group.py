"""add_created_at_and_updated_at_to_chat_group

Revision ID: created_updated_to_chat_group
Revises: created_updated_to_bot_questions
Create Date: 2024-07-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "created_updated_to_chat_group"
down_revision = "created_updated_to_bot_questions"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("chat_group")]

    if "created_at" not in columns:
        op.add_column(
            "chat_group",
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        op.execute("UPDATE chat_group SET created_at = NOW() WHERE created_at IS NULL")

    if "updated_at" not in columns:
        op.add_column(
            "chat_group",
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            ),
        )
        op.execute("UPDATE chat_group SET updated_at = NOW() WHERE updated_at IS NULL")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("chat_group")]

    if "created_at" in columns:
        op.drop_column("chat_group", "created_at")
    if "updated_at" in columns:
        op.drop_column("chat_group", "updated_at")
