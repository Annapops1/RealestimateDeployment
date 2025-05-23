"""Add file fields to ChatMessage

Revision ID: 87b23246c452
Revises: b20bf9120fd6
Create Date: 2025-02-16 20:56:01.442153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87b23246c452'
down_revision = 'b20bf9120fd6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_url', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('file_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('file_type', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.drop_column('file_type')
        batch_op.drop_column('file_name')
        batch_op.drop_column('file_url')

    # ### end Alembic commands ###
