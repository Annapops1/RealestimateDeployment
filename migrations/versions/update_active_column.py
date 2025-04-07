"""Update active column for existing users

Revision ID: update_active_column
Revises: '0919c94cc1aa'
Create Date: 2025-03-18 
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'update_active_column'
down_revision = '0919c94cc1aa'  # Replace with your actual previous migration ID
branch_labels = None
depends_on = None

def upgrade():
    # Update all existing users with NULL active values to True
    op.execute("UPDATE user SET active = TRUE WHERE active IS NULL")

def downgrade():
    # No downgrade needed
    pass 