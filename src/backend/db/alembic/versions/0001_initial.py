"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'folder',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'paper',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('title', sa.String(1024), nullable=False),
        sa.Column('authors', sa.Text()),
        sa.Column('abstract', sa.Text()),
        sa.Column('doi', sa.String(255), unique=True),
        sa.Column('year', sa.Integer()),
        sa.Column('pdf_path', sa.String(1024)),
        sa.Column('user_id', sa.String(64), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('folder_id', sa.String(64), sa.ForeignKey('folder.id')),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'keypoints',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id'), nullable=False, unique=True),
        sa.Column('background', sa.Text()),
        sa.Column('methodology', sa.Text()),
        sa.Column('innovation', sa.Text()),
        sa.Column('conclusion', sa.Text()),
        sa.Column('is_confirmed', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('confirmed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'tag',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
    )

    op.create_table(
        'paper_tag',
        sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id'), primary_key=True),
        sa.Column('tag_id', sa.String(64), sa.ForeignKey('tag.id'), primary_key=True),
    )

    op.create_table(
        'task',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('paper_id', sa.String(64), sa.ForeignKey('paper.id')),
        sa.Column('progress', sa.Integer(), server_default='0', nullable=False),
        sa.Column('result', sa.JSON()),
        sa.Column('error', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('task')
    op.drop_table('paper_tag')
    op.drop_table('tag')
    op.drop_table('keypoints')
    op.drop_table('paper')
    op.drop_table('folder')
    op.drop_table('user')
