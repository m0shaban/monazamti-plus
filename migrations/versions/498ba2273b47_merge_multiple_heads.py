"""merge multiple heads

Revision ID: 498ba2273b47
Revises: 03006a07c749, 3b5c2a9f8123
Create Date: 2025-03-24 11:59:20.448524

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '498ba2273b47'
down_revision = ('03006a07c749', '3b5c2a9f8123')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
