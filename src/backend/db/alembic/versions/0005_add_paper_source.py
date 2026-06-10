"""add source column to paper table

Revision ID: 0005_add_paper_source
Revises: 0004_add_paper_note
Create Date: 2026-05-07

"""
from alembic import op
import sqlalchemy as sa


revision = "0005_add_paper_source"
down_revision = "0004_add_paper_note"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("paper", sa.Column("source", sa.String(512), nullable=True))


def downgrade():
    op.drop_column("paper", "source")
