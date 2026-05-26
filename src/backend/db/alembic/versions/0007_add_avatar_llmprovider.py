"""
add user avatar fields and llm_provider table

Revision ID: 0007_add_avatar_llmprovider
Revises: 0006_add_uix_user_md5
Create Date: 2026-05-25

"""
from alembic import op
import sqlalchemy as sa


revision = "0007_add_avatar_llmprovider"
down_revision = "0006_add_uix_user_md5"
branch_labels = None
depends_on = None


def upgrade():
    # Add avatar columns to user
    op.add_column("user", sa.Column("avatar_path", sa.String(length=1024), nullable=True))
    op.add_column("user", sa.Column("avatar_url", sa.String(length=1024), nullable=True))

    # Create llm_provider table
    op.create_table(
        "llm_provider",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("api_key", sa.String(length=1024), nullable=True),
        sa.Column("default_model", sa.String(length=128), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )


def downgrade():
    op.drop_table("llm_provider")
    op.drop_column("user", "avatar_url")
    op.drop_column("user", "avatar_path")
