"""add paper_note table

Revision ID: 0004_add_paper_note
Revises: 0003_add_paper_embedding
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa


revision = "0004_add_paper_note"
down_revision = "0003_add_paper_embedding"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "paper_note",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("paper_id", sa.String(64), sa.ForeignKey("paper.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("selected_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("paper_note")
