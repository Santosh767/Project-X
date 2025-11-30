import os
from datetime import timedelta
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'hospital.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration - MUST use redis:// protocol
    BROKER_URL = 'redis://localhost:6379/0'
    RESULT_BACKEND = 'redis://localhost:6379/0'
    broker_connection_retry_on_startup = True
    
    # Cache Configuration
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
 
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    #  Google Chat Configuration (Optional)
    GOOGLE_CHAT_WEBHOOK = os.environ.get('GOOGLE_CHAT_WEBHOOK')
    
    # Export Configuration
    EXPORT_FOLDER = os.path.join(basedir, 'exports')
    MAX_EXPORT_AGE_DAYS = 7  # Auto-delete exports older than 7 days