"""Initial migration: create all tables

Revision ID: initial_migration
Revises: 
Create Date: 2025-12-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'category',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), unique=True, nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False)
    )
    op.create_table(
        'game',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('platform_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=False),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('status_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=True),
        sa.Column('ownership_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=True),
        sa.Column('digital_physical_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=True),
        sa.Column('notes', sa.String(length=200), nullable=True),
        sa.Column('image_url', sa.String(length=200), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('purchased_from', sa.String(length=100), nullable=True),
        sa.Column('peripheral_type', sa.String(length=50), nullable=True),
        sa.Column('platform_type', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=20), default="game"),
    )

def downgrade():
    op.drop_table('game')
    op.drop_table('category')
