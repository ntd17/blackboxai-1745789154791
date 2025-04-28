"""Add signature methods

Revision ID: add_signature_methods
Revises: previous_revision
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_signature_methods'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to contracts table
    op.add_column('contracts', sa.Column('signature_method', sa.String(50), nullable=True))
    op.add_column('contracts', sa.Column('token_email', sa.String(255), nullable=True))
    op.add_column('contracts', sa.Column('token_expiry', sa.DateTime, nullable=True))
    op.add_column('contracts', sa.Column('certificate_info', postgresql.JSONB, nullable=True))

    # Add settings table for admin configurations
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key', sa.String(255), unique=True, nullable=False),
        sa.Column('value', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )

    # Insert default signature method
    op.execute(
        "INSERT INTO settings (key, value, created_at, updated_at) VALUES "
        "('default_signature_method', 'signature_click_only', NOW(), NOW())"
    )

def downgrade():
    # Remove new columns from contracts table
    op.drop_column('contracts', 'signature_method')
    op.drop_column('contracts', 'token_email')
    op.drop_column('contracts', 'token_expiry')
    op.drop_column('contracts', 'certificate_info')

    # Drop settings table
    op.drop_table('settings')
