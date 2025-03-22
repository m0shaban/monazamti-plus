import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secure-secret-key'
    
    # Add support for Railway MySQL database
    database_url = (
        os.environ.get('MYSQL_URL') or 
        os.environ.get('RAILWAY_DATABASE_URL') or 
        os.environ.get('DATABASE_URL') or 
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/db.sqlite')
    )
    
    if database_url and database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://")
    elif database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://")
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
