from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0011_add_graph_llm_cache"
down_revision = "0010_add_graph_editing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "graph_llm_cache",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("folder_id", sa.String(64), nullable=True, index=True),
        sa.Column("papers_hash", sa.String(64), nullable=False),
        sa.Column("clusters", mysql.JSON, nullable=False),
        sa.Column("nodes", mysql.JSON, nullable=False),
        sa.Column("edges", mysql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("graph_llm_cache")