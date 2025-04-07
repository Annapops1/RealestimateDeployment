"""merge heads

Revision ID: 086190fc361a
Revises: 0fb77505ab4d, 8aeda4723508, add_wishlist_property_rel, merge_multiple_heads
Create Date: 2025-02-16 14:03:51.300180

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '086190fc361a'
down_revision = ('0fb77505ab4d', '8aeda4723508', 'add_wishlist_property_rel', 'merge_multiple_heads')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
