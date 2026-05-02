"""add paper_embedding table (MySQL JSON)

Revision ID: 0003_add_paper_embedding
Revises: 0002_add_md5_hash_file_size
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_paper_embedding"
down_revision = "0002_add_md5_hash_file_size"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "paper_embedding",
        sa.Column("paper_id", sa.String(64), sa.ForeignKey("paper.id"), primary_key=True),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("paper_embedding")
