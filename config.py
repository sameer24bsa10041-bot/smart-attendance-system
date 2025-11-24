import os
from datetime import timedelta

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'attendance.db')
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT', 5))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 60))
    
    # Features
    ENABLE_FACE_RECOGNITION = os.environ.get('ENABLE_FACE_RECOGNITION', 'true').lower() == 'true'
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL', 'false').lower() == 'true'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests