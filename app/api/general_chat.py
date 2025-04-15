from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import logging

from app.utils.api_utils import APIError, log_api_access

# Set up logging
logger = logging.getLogger(__name__)

general_chat_bp = Blueprint('general_chat', __name__, url_prefix='/api/general_chat')

@general_chat_bp.route('/', methods=['POST'])
@login_required
def chat_with_ai():
    """Chat with AI without document context"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("Missing request data", code=400)
            
        if 'query' not in data:
            raise APIError("Missing required parameter: query", code=400)
            
        query = data.get('query')
        
        # Get AI service
        ai_service = current_app.services.get('ai_service')
        if not ai_service:
            raise APIError("AI service unavailable", code=503)
            
        # Generate general response
        response = generate_general_response(ai_service, query)
        
        if not response:
            raise APIError("Failed to generate response", code=500)
            
        log_api_access("general_chat", True, {
            "query_length": len(query)
        })
            
        return jsonify({
            'response': response,
            'is_fallback': False
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error in general chat")
        log_api_access("general_chat", False, {})
        raise APIError.from_exception(e, default_message="Failed to process chat request")

def generate_general_response(ai_service, query):
    """Generate a response to a general question using the AI service"""
    try:
        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        
        # Define a system prompt
        system_prompt = """You are a helpful AI assistant built into a study application.
You can help with studying, learning, and general knowledge questions.
Provide concise, accurate responses."""
        
        # Make API call
        result = ai_service._call_claude_api(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7
        )
        
        # Extract response
        if 'content' in result and len(result['content']) > 0:
            response = result['content'][0]['text'].strip()
            return response
        else:
            logger.error("Invalid response from AI service")
            return None
            
    except Exception as e:
        logger.exception(f"Error generating general response: {str(e)}")
        return None 