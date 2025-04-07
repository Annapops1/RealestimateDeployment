"""add chat message columns

Revision ID: 2024_03_21_chat_msg
Create Date: 2024-03-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '2024_03_21_chat_msg'
down_revision = '8aeda4723508'  # Points to property images migration
branch_labels = None
depends_on = None

def upgrade():
    # existing upgrade logic
    pass

def downgrade():
    # existing downgrade logic
    pass 