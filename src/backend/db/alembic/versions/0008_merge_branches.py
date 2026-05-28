"""
merge avatar and fulltext branches

Revision ID: 0008_merge_branches
Revises: 0007_add_avatar_llmprovider, 0007_add_fulltext_search
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa


revision = "0008_merge_branches"
down_revision = "0007_add_avatar_llmprovider"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
