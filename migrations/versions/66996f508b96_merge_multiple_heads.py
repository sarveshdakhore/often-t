"""
Revision ID: 66996f508b96
Revises: add_description_column, add_template_flag_day_models
Create Date: 2025-05-01 18:01:12.143170

"""

# revision identifiers, used by Alembic.
revision = '66996f508b96'
down_revision = ('add_description_column', 'add_template_flag_day_models')
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass

def downgrade():
    pass
