"""add template flag to day models

Revision ID: add_template_flag_day_models
Revises: e555fc0a3908
Create Date: 2025-05-01 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_template_flag_day_models'
down_revision = 'e555fc0a3908'  # Set this to your latest migration
branch_labels = None
depends_on = None

def upgrade():
    # Add template column to day_hotels if it doesn't exist already
    try:
        op.add_column('day_hotels', sa.Column('template', sa.Boolean(), nullable=False, server_default=sa.false()))
    except Exception as e:
        print(f"Could not add template to day_hotels, might already exist: {e}")
    
    # Add template column to day_activities if it doesn't exist already
    try:
        op.add_column('day_activities', sa.Column('template', sa.Boolean(), nullable=False, server_default=sa.false()))
    except Exception as e:
        print(f"Could not add template to day_activities, might already exist: {e}")
        
    # Add template column to day_transfers if it doesn't exist already
    try:
        op.add_column('day_transfers', sa.Column('template', sa.Boolean(), nullable=False, server_default=sa.false()))
    except Exception as e:
        print(f"Could not add template to day_transfers, might already exist: {e}")

def downgrade():
    # Remove template columns if they exist
    try:
        op.drop_column('day_hotels', 'template')
    except Exception:
        pass
        
    try:
        op.drop_column('day_activities', 'template')
    except Exception:
        pass
        
    try:
        op.drop_column('day_transfers', 'template')
    except Exception:
        pass
