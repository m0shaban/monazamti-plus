"""Add primary_color field to UserSettings

Revision ID: 4d2c7a5b8123
Revises: 3b5c2a9f8123
Create Date: 2023-06-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d2c7a5b8123'
down_revision = '3b5c2a9f8123'  # Make sure this points to your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Add primary_color column to user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('primary_color', sa.String(length=20), nullable=True))
            # Set default value for existing records
            op.execute("UPDATE user_settings SET primary_color = '#4e73df' WHERE primary_color IS NULL")
        except Exception as e:
            print(f"Error adding primary_color column: {str(e)}")
            # Column may already exist or other issue


def downgrade():
    # Remove primary_color column from user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.drop_column('primary_color')
