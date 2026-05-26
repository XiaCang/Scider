"""
add fulltext index for paper search

Revision ID: 0007_add_fulltext_search
Revises: 0006_add_uix_user_md5
Create Date: 2026-05-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "0007_add_fulltext_search"
down_revision = "0006_add_uix_user_md5"
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加 full_text 字段存储 PDF 完整文本
    op.add_column('paper', sa.Column('full_text', mysql.LONGTEXT(), nullable=True, comment='PDF 完整文本内容'))
    
    # 2. 创建 FULLTEXT 索引（使用 ngram 分词器）
    # 注意：需要在 MySQL 配置中设置 ngram_token_size = 2
    op.execute(sa.text(
        "ALTER TABLE `paper` ADD FULLTEXT INDEX `ft_idx_full_text` (`full_text`) WITH PARSER ngram"
    ))


def downgrade():
    # 1. 删除 FULLTEXT 索引
    op.execute(sa.text("ALTER TABLE `paper` DROP INDEX `ft_idx_full_text`"))
    
    # 2. 删除 full_text 字段
    op.drop_column('paper', 'full_text')
