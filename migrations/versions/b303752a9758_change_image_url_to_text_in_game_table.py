"""Change image_url to Text in game table

Revision ID: b303752a9758
Revises: a144cdae5a0e
Create Date: 2025-12-16 08:20:15.200256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b303752a9758'
down_revision = 'a144cdae5a0e'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('game', 'image_url',
        existing_type=sa.String(length=200),
        type_=sa.Text(),
        existing_nullable=True
    )

def downgrade():
    op.alter_column('game', 'image_url',
        existing_type=sa.Text(),
        type_=sa.String(length=200),
        existing_nullable=True
    )
