"""add property verification fields

Revision ID: e5eeeea733eb
Revises: 33cd25ce1cfd
Create Date: 2025-03-11 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5eeeea733eb'
down_revision = '33cd25ce1cfd'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns first
    op.add_column('property', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('property', sa.Column('verification_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('property', sa.Column('admin_feedback', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.add_column('property', sa.Column('verified_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraint with explicit name
    with op.batch_alter_table('property') as batch_op:
        batch_op.create_foreign_key(
            'fk_property_verified_by_user',
            'user',
            ['verified_by'],
            ['id']
        )


def downgrade():
    # Remove foreign key constraint first
    with op.batch_alter_table('property') as batch_op:
        batch_op.drop_constraint('fk_property_verified_by_user', type_='foreignkey')
    
    # Then remove columns
    op.drop_column('property', 'verified_by')
    op.drop_column('property', 'verified_at')
    op.drop_column('property', 'admin_feedback')
    op.drop_column('property', 'verification_status')
    op.drop_column('property', 'is_verified')
