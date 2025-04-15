from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import logging

from app import db
from app.models.document import Document
from app.utils.api_utils import APIError, log_api_access

# Set up logging
logger = logging.getLogger(__name__)

document_chat_bp = Blueprint('document_chat', __name__, url_prefix='/api/document_chat')

@document_chat_bp.route('/question', methods=['POST'])
@login_required
def chat_with_document():
    """Chat with a document using Claude API"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("Missing request data", code=400)
            
        if 'document_id' not in data or 'question' not in data:
            raise APIError("Missing required parameters (document_id, question)", code=400)
            
        document_id = data.get('document_id')
        question = data.get('question')
        chat_history = data.get('chat_history', [])
        
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            raise APIError("Document not found", code=404)
            
        # Get document text
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
            
        text = document_processor._extract_document_text(document)
        
        if not text:
            raise APIError("Failed to extract document text", code=500)
            
        # Get AI service to process chat
        ai_service = current_app.services.get('ai_service')
        if not ai_service:
            raise APIError("AI service unavailable", code=503)
            
        # Process chat with text
        answer = ai_service.chat_with_text(text, question, chat_history)
        
        if not answer:
            raise APIError("Failed to generate response", code=500)
            
        log_api_access("chat_with_document", True, {
            "document_id": document_id,
            "question_length": len(question)
        })
            
        return jsonify({
            'answer': answer,
            'document_id': document_id,
            'is_fallback': False  # Can be enhanced to detect fallback responses
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error in document chat")
        log_api_access("chat_with_document", False, {
            "document_id": data.get('document_id') if data else None
        })
        raise APIError.from_exception(e, default_message="Failed to process chat request")