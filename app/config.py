import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_DEBUG') == '1' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

class Config:
    """Base configuration class"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database optimization
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # API Keys
    COHERE_API_KEY = os.environ.get('COHERE_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Memory management
    EMBED_BATCH_SIZE = 5
    MAX_CHUNK_SIZE = 300
    MAX_OVERLAP = 50
    MAX_TEXT_LENGTH = 50000
    MAX_PDF_PAGES = 10
    
    # Error logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    # Debug settings
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Use more secure settings for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Enable SSL in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False