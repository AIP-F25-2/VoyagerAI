import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEFAULT_DATABASE_URI = 'sqlite:///voyagerai.db'

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', DEFAULT_DATABASE_URI)
    
    # Scraping configuration
    SCRAPING_TIMEOUT = int(os.getenv('SCRAPING_TIMEOUT', 60))
    MAX_EVENTS_PER_CITY = int(os.getenv('MAX_EVENTS_PER_CITY', 1000))  # Increased from 100 to 1000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', DEFAULT_DATABASE_URI)

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', DEFAULT_DATABASE_URI)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
