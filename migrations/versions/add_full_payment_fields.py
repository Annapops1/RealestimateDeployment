"""add full payment fields

Revision ID: 2024_03_21_full_payment
Create Date: 2024-03-21
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '2024_03_21_full_payment'
down_revision = '2024_03_21_chat_msg'  # Points to chat messages migration
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('contract', schema=None) as batch_op:
        batch_op.add_column(sa.Column('full_payment_made', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('full_payment_date', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('contract', schema=None) as batch_op:
        batch_op.drop_column('full_payment_date')
        batch_op.drop_column('full_payment_made') 