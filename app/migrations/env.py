from alembic import context
from app import create_app, db
from app.models import *

app = create_app()
config = context.config
target_metadata = db.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    with app.app_context():
        with db.engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()
