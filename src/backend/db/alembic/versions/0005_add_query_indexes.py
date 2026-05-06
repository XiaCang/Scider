"""add indexes for graph/list queries

Revision ID: 0005_add_query_indexes
Revises: 0004_add_paper_note
Create Date: 2026-05-06

"""
from alembic import op


revision = "0005_add_query_indexes"
down_revision = "0004_add_paper_note"
branch_labels = None
depends_on = None


def upgrade():
    # 按用户 + 时间拉论文列表；按用户 + 文件夹过滤图谱
    op.create_index("ix_paper_user_created", "paper", ["user_id", "created_at"], unique=False)
    op.create_index("ix_paper_user_folder", "paper", ["user_id", "folder_id"], unique=False)
    # ORDER BY paper_embedding.updated_at DESC
    op.create_index("ix_paper_embedding_updated_at", "paper_embedding", ["updated_at"], unique=False)


def downgrade():
    op.drop_index("ix_paper_embedding_updated_at", table_name="paper_embedding")
    op.drop_index("ix_paper_user_folder", table_name="paper")
    op.drop_index("ix_paper_user_created", table_name="paper")
