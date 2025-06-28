import os
from dotenv import load_dotenv
from datetime import timedelta
from sqlalchemy import MetaData

load_dotenv()

# Add naming conventions to avoid "Constraint must have a name" migration errors.
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

# Ensure that your Flask-SQLAlchemy is initialized with this metadata, for example:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy(metadata=metadata)

class Config:
    # Ensure the path is absolute and the directory exists
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASEDIR, 'instance')
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-replace-in-production'
    
    # Enable Flask debugging if in development mode
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Other configuration settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'app', 'static', 'uploads')
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # If using PostgreSQL with Koyeb and DATABASE_URL starts with postgres://, replace it with postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
