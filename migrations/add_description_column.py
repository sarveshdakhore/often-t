from alembic import op
import sqlalchemy as sa

# Revision identifier
revision = 'add_description_column'
down_revision = None  # Replace with your previous migration ID

def upgrade():
    op.add_column('activities', sa.Column('description', sa.String(), nullable=True))

def downgrade():
    op.drop_column('activities', 'description')
