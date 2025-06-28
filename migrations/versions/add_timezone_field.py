"""Add timezone field to UserSettings

Revision ID: 3b5c2a9f8123
Revises: 
Create Date: 2023-05-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b5c2a9f8123'
down_revision = None  # Replace with the previous migration ID if needed
branch_labels = None
depends_on = None


def upgrade():
    # Add timezone column to user_settings table if it doesn't exist
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('timezone', sa.String(length=50), nullable=True))
            # Set default value for existing records
            op.execute("UPDATE user_settings SET timezone = 'UTC' WHERE timezone IS NULL")
        except:
            pass  # Column may already exist


def downgrade():
    # Remove timezone column from user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.drop_column('timezone')
