import logging
from app.services.document_processor import DocumentProcessor
from app.services.claude_service import ClaudeService
from app.services.question_generator import QuestionGenerator
from app.services.document_chatbot import DocumentChatbot
from app.services.study_assistant import StudyAssistant
from app.services.embeddings import EmbeddingsService

# Set up logging
logger = logging.getLogger(__name__)

def initialize_services(app):
    """Initialize and register all services in the app's service container"""
    logger.info("Initializing services...")
    
    # Register document processor
    app.services.register(
        'document_processor',
        DocumentProcessor(
            upload_folder=app.config['UPLOAD_FOLDER'],
            allowed_extensions=app.config['ALLOWED_EXTENSIONS']
        )
    )
    
    # Register Claude service for OCR and chat
    app.services.register(
        'ai_service',
        ClaudeService(
            api_key=app.config['ANTHROPIC_API_KEY']
        )
    )
    
    # Register question generator
    app.services.register(
        'question_generator',
        QuestionGenerator(
            api_key=app.config['ANTHROPIC_API_KEY']
        )
    )
    
    # Register document chatbot
    app.services.register(
        'document_chatbot',
        DocumentChatbot(
            api_key=app.config['ANTHROPIC_API_KEY']
        )
    )
    
    # Register study assistant
    app.services.register(
        'study_assistant',
        StudyAssistant(
            api_key=app.config['ANTHROPIC_API_KEY']
        )
    )
    
    # Register embeddings service for semantic search
    app.services.register(
        'embeddings_service',
        EmbeddingsService(
            api_key=app.config['ANTHROPIC_API_KEY']
        )
    )
    
    logger.info("Services initialized and registered") 