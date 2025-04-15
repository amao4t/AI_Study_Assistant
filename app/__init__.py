from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)
    ]
)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth_views.login'

class ServiceContainer:
    """Container for service dependencies"""
    def __init__(self):
        self.services = {}
        logger.info("Initialized ServiceContainer")
        
    def register(self, name, service):
        """Register a service"""
        self.services[name] = service
        logger.debug(f"Registered service: {name}")
        
    def get(self, name):
        """Get a service by name"""
        service = self.services.get(name)
        if not service:
            logger.warning(f"Service not found: {name}")
        return service

def create_app(config_class='app.config.DevelopmentConfig'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    logger.info("Initializing app with config: %s", config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)
    
    # Create necessary directories
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info("Created upload folder: %s", app.config['UPLOAD_FOLDER'])
    
    # Initialize service container
    services = ServiceContainer()
    
    # Register API blueprints
    from app.api.auth import auth_bp
    from app.api.documents import documents_bp
    from app.api.questions import questions_bp
    from app.api.text import text_bp
    from app.api.study import study_bp
    from app.api.document_chat import document_chat_bp
    from app.api.general_chat import general_chat_bp

    app.register_blueprint(document_chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(text_bp)
    app.register_blueprint(study_bp)
    app.register_blueprint(general_chat_bp)
    
    # Register route blueprints for templates
    from app.routes import main_bp
    from app.auth_routes import auth_routes_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_routes_bp)
    
    # Initialize service container
    app.services = services
    
    # Initialize services
    from app.services.service_factory import initialize_services
    initialize_services(app)
    
    # Initialize login manager
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register error handlers
    from app.utils.api_utils import APIError
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return error.to_response()
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error: %s", str(error))
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {'error': 'File too large. Maximum file size is 10MB.'}, 413
        
    logger.info("App initialization complete")
    
    return app