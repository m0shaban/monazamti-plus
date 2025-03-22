import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sk-191a0bcb7a3d4a85b8ddd42373212426'
    
    # دعم عدة أنواع من قواعد البيانات بما فيها Koyeb
    database_url = (
        os.environ.get('DATABASE_URL') or
        os.environ.get('KOYEB_PSQL_URL') or
        os.environ.get('PSQL_URL') or
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance/db.sqlite')
    )
    
    # تحويل عنوان Postgres إلى الصيغة الصحيحة
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات البريد الإلكتروني (اختياري)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
