from flask import Blueprint
from app import db

# Initialize auth blueprint
bp = Blueprint('auth', __name__)

# Try to setup Flask-Security if available
try:
    from flask_security import Security, SQLAlchemySessionUserDatastore
    from app.models import User, Role
    
    # Setup Flask-Security
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security = Security(datastore=user_datastore)
except ImportError:
    # Flask-Security is not installed, continue without it
    pass

# Import routes after initialization to avoid circular imports
from app.auth import routes
