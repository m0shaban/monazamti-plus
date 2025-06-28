from flask import Blueprint

bp = Blueprint('main', __name__)

# Import routes after bp is defined to avoid circular imports
from app.main import routes
