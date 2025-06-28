"""merge multiple heads

Revision ID: e9b99f4dbe2c
Revises: 498ba2273b47, 4d2c7a5b8123
Create Date: 2025-03-24 12:06:58.360489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9b99f4dbe2c'
down_revision = ('498ba2273b47', '4d2c7a5b8123')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
