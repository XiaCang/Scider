"""
add graph_node and graph_edge tables for custom graph editing

Revision ID: 0010_add_graph_editing
Revises: 0009_add_notes_tables
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0010_add_graph_editing"
down_revision = "0009_add_notes_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "graph_node",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("paper_id", sa.String(64), sa.ForeignKey("paper.id"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("node_type", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("category", sa.Integer, nullable=False, server_default="0"),
        sa.Column("properties", mysql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "graph_edge",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("graph_node.id"), nullable=False, index=True),
        sa.Column("target_id", sa.String(64), sa.ForeignKey("graph_node.id"), nullable=False, index=True),
        sa.Column("relation_type", sa.String(50), nullable=False, server_default="related"),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("properties", mysql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("graph_edge")
    op.drop_table("graph_node")
