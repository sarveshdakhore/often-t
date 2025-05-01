"""Add description column to activities table

Revision ID: add_description_to_activities
Revises: <previous_revision_id>  # Replace with your latest revision ID
Create Date: 2023-07-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_description_to_activities'
down_revision = '<previous_revision_id>'  # Replace with your latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('description', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'description')
