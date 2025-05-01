"""Add description column to activities table

Revision ID: add_description_column
Revises: 
Create Date: 2025-05-01 17:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_description_column'
down_revision = None  # Replace with your previous migration ID if needed

def upgrade():
    op.add_column('activities', sa.Column('description', sa.String(), nullable=True))

def downgrade():
    op.drop_column('activities', 'description')
