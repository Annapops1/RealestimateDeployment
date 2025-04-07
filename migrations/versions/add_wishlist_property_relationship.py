"""Add wishlist property relationship

Revision ID: add_wishlist_property_rel
Revises: previous_migration_id
Create Date: 2024-02-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_wishlist_property_rel'
down_revision = None  # Replace with your last migration ID
branch_labels = None
depends_on = None

def upgrade():
    # No changes needed in the database schema
    # The relationship is only added at the SQLAlchemy model level
    pass

def downgrade():
    # No changes needed as we're only adding a relationship
    pass 