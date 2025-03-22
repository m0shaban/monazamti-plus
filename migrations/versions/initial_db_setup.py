"""Initial database setup

Revision ID: initial_setup
Revises: 
Create Date: 2024-03-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'initial_setup'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create tables with proper MySQL types
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # ...remaining table creation code...

def downgrade():
    op.drop_table('user')
    # ...remaining table drop code...
