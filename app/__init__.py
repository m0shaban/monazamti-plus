from flask import Flask, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import datetime
import os
import logging
import pytz
from werkzeug.exceptions import BadRequest

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Security enhancements for session cookies
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)  # Session expiration
    
    # Conditionally turn off secure cookies in development to allow local testing
    if app.debug:
        app.config['SESSION_COOKIE_SECURE'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Initialize security features
    from app.utils.security import RequestLogger
    request_logger = RequestLogger(app)
    
    # Set up login manager
    login_manager.login_view = 'auth.login'  # This MUST match the blueprint name 'auth'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Ensure instance folder exists and configure paths
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    instance_path = os.path.join(base_dir, 'instance')
    
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        logger.info(f"Created instance directory at {instance_path}")
    
    # Override SQLAlchemy database URI with absolute path
    db_path = os.path.join(instance_path, 'site.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    logger.info(f"Using database at: {db_path}")
    
    # Set login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'info'
    
    # Error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    @app.context_processor
    def inject_globals():
        # Generate CSRF token once per request and provide as string
        csrf = generate_csrf()
        ctx = {
            'csrf_token': csrf,
            'now': datetime.datetime.now()
        }
        
        # Apply user timezone if available
        if 'timezone' in session:
            try:
                tz = pytz.timezone(session['timezone'])
                ctx['now'] = datetime.datetime.now(tz)
            except:
                pass
        
        return ctx
    
    @app.before_request
    def validate_request():
        """
        Middleware to validate incoming HTTP requests and handle malformed ones
        """
        from app.utils.security import validate_request
        from flask import request, abort
        
        # Block obviously malformed requests (like "TP/1.1")
        if not validate_request():
            logger.warning(f"Blocked malformed request from {request.remote_addr}: {request.environ.get('SERVER_PROTOCOL', 'Unknown protocol')}")
            return render_template('errors/400.html'), 400
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html'), 400
    
    @app.before_request
    def before_request():
        # Set user's timezone in session
        if current_user.is_authenticated:
            # Ensure user has settings
            if hasattr(current_user, 'settings') and current_user.settings:
                session['timezone'] = current_user.settings.timezone
                session['theme'] = current_user.settings.theme
                session['primary_color'] = current_user.settings.primary_color
                session['compact_mode'] = current_user.settings.compact_mode
            else:
                # Create default settings if not exist
                from app.models import UserSettings
                try:
                    settings = UserSettings(user_id=current_user.id)
                    db.session.add(settings)
                    db.session.commit()
                    current_user.settings = settings
                    session['timezone'] = settings.timezone
                    session['theme'] = settings.theme
                    session['primary_color'] = settings.primary_color
                    session['compact_mode'] = settings.compact_mode
                except Exception as e:
                    logger.error(f"Error creating user settings: {e}")
        
        # Check if the user is authenticated and has settings
        if current_user.is_authenticated and hasattr(current_user, 'settings') and current_user.settings is not None:
            # Set user preferences in session
            session['timezone'] = getattr(current_user.settings, 'timezone', 'UTC')
            session['language'] = getattr(current_user.settings, 'language', 'ar')
            session['theme'] = getattr(current_user.settings, 'theme', 'light')
            session['primary_color'] = getattr(current_user.settings, 'primary_color', '#4e73df')
        else:
            # Set default preferences
            session['timezone'] = 'UTC'
            session['language'] = 'ar'
            session['theme'] = 'light'
            session['primary_color'] = '#4e73df'
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(429)
    def ratelimit_error(error):
        logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app

from app import models
