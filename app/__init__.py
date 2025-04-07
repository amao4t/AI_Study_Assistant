from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth_views.login'

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
    import os
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info("Created upload folder: %s", app.config['UPLOAD_FOLDER'])
    
    # Register API blueprints
    from app.api.auth import auth_bp
    from app.api.documents import documents_bp
    from app.api.questions import questions_bp
    from app.api.text import text_bp
    from app.api.study import study_bp
    from app.api.document_chat import document_chat_bp

    app.register_blueprint(document_chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(text_bp)
    app.register_blueprint(study_bp)
    
    # Register route blueprints for templates
    from app.routes import main_bp
    from app.auth_routes import auth_routes_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_routes_bp)
    
    # Register error handlers
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