"""add md5_hash and file_size to paper

Revision ID: 0002_add_md5_hash_file_size
Revises: 0001_initial
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_md5_hash_file_size"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("paper") as batch_op:
        batch_op.add_column(sa.Column("md5_hash", sa.String(64), unique=True, nullable=True))
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch_op.create_index("ix_paper_md5_hash", ["md5_hash"])


def downgrade():
    with op.batch_alter_table("paper") as batch_op:
        batch_op.drop_index("ix_paper_md5_hash")
        batch_op.drop_column("file_size")
        batch_op.drop_column("md5_hash")
