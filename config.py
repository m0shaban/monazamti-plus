import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secure-secret-key'
    
    # تكوين قاعدة البيانات
    mysql_url = os.environ.get('MYSQL_URL')
    if mysql_url:
        # تحويل عنوان MySQL إلى صيغة SQLAlchemy
        database_url = mysql_url.replace('mysql://', 'mysql+pymysql://')
    else:
        database_url = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/db.sqlite')
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
