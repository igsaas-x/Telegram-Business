"""add_registered_by_column_to_chat_group

Revision ID: j5k6l7m8n9o0
Revises: 9a6539a7f2ba
Create Date: 2025-08-12 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n9o0'
down_revision = '9a6539a7f2ba'
branch_labels = None
depends_on = None


def upgrade():
    # Add registered_by column to chat_group table
    op.add_column('chat_group', sa.Column('registered_by', sa.String(20), nullable=True))


def downgrade():
    # Remove registered_by column from chat_group table
    op.drop_column('chat_group', 'registered_by')