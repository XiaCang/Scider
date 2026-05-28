"""
add notes tables and columns for richtext and images

Revision ID: 0009_add_notes_tables
Revises: 0008_add_fulltext_search
Create Date: 2026-05-28

"""
from alembic import op
import sqlalchemy as sa

revision = '0009_add_notes_tables'
down_revision = '0008_merge_branches'
branch_labels = None
depends_on = None


def upgrade():
    # 在 paper_note 表添加列
    op.add_column('paper_note', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('paper_note', sa.Column('content_html', sa.Text(), nullable=True))
    op.add_column('paper_note', sa.Column('content_format', sa.String(length=20), nullable=False, server_default='html'))
    op.add_column('paper_note', sa.Column('content_text', sa.Text(), nullable=True))

    # 创建 note_image 表
    op.create_table(
        'note_image',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('note_id', sa.String(length=64), sa.ForeignKey('paper_note.id'), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('mime_type', sa.String(length=50), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # 创建 note_search 表
    op.create_table(
        'note_search',
        sa.Column('note_id', sa.String(length=64), sa.ForeignKey('paper_note.id'), primary_key=True),
        sa.Column('paper_id', sa.String(length=64), nullable=False),
        sa.Column('note_title', sa.String(length=255), nullable=True),
        sa.Column('paper_title', sa.String(length=1024), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 为 note_search 创建 FULLTEXT 索引（MySQL），使用 raw SQL
    op.execute(sa.text('ALTER TABLE `note_search` ADD FULLTEXT `ft_note_search` (`note_title`, `paper_title`, `content_text`)'))


def downgrade():
    try:
        op.execute(sa.text('ALTER TABLE `note_search` DROP INDEX `ft_note_search`'))
    except Exception:
        pass

    op.drop_table('note_search')
    op.drop_table('note_image')

    op.drop_column('paper_note', 'content_text')
    op.drop_column('paper_note', 'content_format')
    op.drop_column('paper_note', 'content_html')
    op.drop_column('paper_note', 'title')
