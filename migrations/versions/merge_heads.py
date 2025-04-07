"""merge heads

Revision ID: merge_multiple_heads
Revises: head1, head2  # Replace with your actual head revision IDs
Create Date: 2024-02-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_multiple_heads'
# Replace head1, head2 with the actual revision IDs from 'flask db heads'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass 