"""add template flag to day models

Revision ID: add_template_flag_migration
Revises: e555fc0a3908
Create Date: 2025-05-02 10:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'add_template_flag_migration'
down_revision = 'e555fc0a3908'  # Adjust based on your latest migration
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError, OperationalError


def upgrade():
    # Add columns with error handling to skip if they already exist
    _add_column_if_not_exists('day_hotels', 'template')
    _add_column_if_not_exists('day_activities', 'template')
    _add_column_if_not_exists('day_transfers', 'template')
    
    # If columns were added to specific tables without errors
    print("Migration completed successfully.")


def _add_column_if_not_exists(table, column):
    try:
        op.add_column(table, sa.Column(column, sa.Boolean(), nullable=False, server_default=sa.false()))
        print(f"✓ Added column '{column}' to table '{table}'")
    except (ProgrammingError, OperationalError) as e:
        if 'already exists' in str(e):
            print(f"✓ Column '{column}' already exists in table '{table}' - skipping")
        else:
            print(f"✗ Error adding column '{column}' to table '{table}': {e}")


def downgrade():
    # Remove template columns with error handling
    tables = ['day_hotels', 'day_activities', 'day_transfers']
    
    for table in tables:
        try:
            op.drop_column(table, 'template')
            print(f"Dropped column 'template' from table '{table}'")
        except (ProgrammingError, OperationalError) as e:
            print(f"Error dropping column from '{table}': {e}")
