"""
add user+md5 unique constraint to paper

Revision ID: 0006_add_uix_user_md5
Revises: 0005_add_paper_source
Create Date: 2026-05-11

"""
from alembic import op
import sqlalchemy as sa


revision = "0006_add_uix_user_md5"
down_revision = "0005_add_paper_source"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # If there is an existing unique index on md5_hash, drop it.
    idx_query = sa.text(
        "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='paper' "
        "AND COLUMN_NAME='md5_hash' AND NON_UNIQUE=0 LIMIT 1"
    )
    res = conn.execute(idx_query)
    row = res.fetchone()
    if row:
        idx_name = row[0]
        op.execute(sa.text(f"ALTER TABLE `paper` DROP INDEX `{idx_name}`"))

    # Create composite unique constraint (user_id, md5_hash)
    op.create_unique_constraint('uix_user_md5', 'paper', ['user_id', 'md5_hash'])


def downgrade():
    # Drop composite constraint
    op.drop_constraint('uix_user_md5', 'paper', type_='unique')

    # Recreate single-column unique constraint on md5_hash
    op.create_unique_constraint('uq_paper_md5_hash', 'paper', ['md5_hash'])
