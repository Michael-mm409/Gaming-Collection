"""Add peripheral table

Revision ID: c9336234feb1
Revises: initial_migration
Create Date: 2025-12-15 14:53:05.551059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9336234feb1'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'peripheral',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('platform_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=False),
        sa.Column('peripheral_type', sa.String(length=50), nullable=True),
        sa.Column('platform_type', sa.String(length=50), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('purchased_from', sa.String(length=100), nullable=True),
        sa.Column('ownership_id', sa.Integer(), sa.ForeignKey('category.id'), nullable=True),
        sa.Column('notes', sa.String(length=200), nullable=True),
   )

def downgrade():
   op.drop_table('peripheral')
