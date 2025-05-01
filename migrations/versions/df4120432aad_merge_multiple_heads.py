"""
Revision ID: df4120432aad
Revises: 66996f508b96, add_template_flag_migration
Create Date: 2025-05-01 18:46:55.289584

"""

# revision identifiers, used by Alembic.
revision = 'df4120432aad'
down_revision = ('66996f508b96', 'add_template_flag_migration')
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass

def downgrade():
    pass
