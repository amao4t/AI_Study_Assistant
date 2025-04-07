from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import logging
import requests
import json

from app import db
from app.models.document import Document
from app.utils.api_utils import safe_api_call

# Set up logging
logger = logging.getLogger(__name__)

document_chat_bp = Blueprint('document_chat', __name__, url_prefix='/api/document-chat')

@document_chat_bp.route('/<int:document_id>', methods=['POST'])
@login_required
def chat_with_document(document_id):
    """Chat with a document using Claude API"""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    # Check if document exists and belongs to user
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found or you don\'t have permission'}), 404
    
    document.update_last_accessed()
    
    # Get document text from document processor service
    from app.services.document_processor import DocumentProcessor
    processor = DocumentProcessor(
        upload_folder=current_app.config['UPLOAD_FOLDER'],
        allowed_extensions=current_app.config['ALLOWED_EXTENSIONS']
    )
    
    document_text, error = processor.get_document_text(document_id)
    if error:
        return jsonify({'error': f'Error getting document text: {error}'}), 400
    
    # Get chat history from request
    chat_history = data.get('chat_history', [])
    
    # Generate response using Claude API with improved error handling
    response, is_fallback, error = safe_api_call(
        chat_with_claude,
        document_text=document_text,
        user_question=data.get('question'),
        chat_history=chat_history,
        api_key=current_app.config.get('ANTHROPIC_API_KEY'),
        service_name="Claude Document Chat",
        fallback_func=get_document_chat_fallback
    )
    
    if error and not response:
        return jsonify({'error': error}), 400
    
    # Update chat history
    chat_history.append({'role': 'user', 'message': data.get('question')})
    chat_history.append({'role': 'assistant', 'message': response})
    
    return jsonify({
        'response': response,
        'chat_history': chat_history,
        'is_fallback': is_fallback
    }), 200

def chat_with_claude(document_text, user_question, chat_history, api_key):
    """Direct implementation of Claude API chat with document"""
    logger.info(f"Processing chat: document length {len(document_text)}, question length {len(user_question)}")
    
    if not api_key:
        raise ValueError("API key not configured")
    
    # Truncate document text if too long
    max_length = 5000
    if len(document_text) > max_length:
        logger.warning(f"Document too long ({len(document_text)} chars), truncating to {max_length}")
        document_text = document_text[:max_length]
    
    # Prepare API endpoint and headers
    api_url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Format the user's first message with the document
    first_message = f"""
I'll be asking questions about the following document:

{document_text}

Please only use information contained in this document to answer my questions.
    """
    
    # Prepare the messages array
    messages = [
        {"role": "user", "content": first_message}
    ]
    
    # Add a simulated assistant acknowledgement
    messages.append({
        "role": "assistant", 
        "content": "I've reviewed the document and I'm ready to answer questions based on its content."
    })
    
    # Add chat history (limited to recent interactions)
    if chat_history and len(chat_history) > 0:
        # Limit to 3 most recent exchanges to avoid token limits
        recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
        for message in recent_history:
            role = "user" if message.get("role") == "user" else "assistant"
            # Truncate long messages
            content = message.get("message", "")
            if len(content) > 1000:
                content = content[:1000] + "... [truncated]"
            messages.append({"role": role, "content": content})
    
    # Add the current question
    messages.append({"role": "user", "content": user_question})
    
    # Prepare the request payload
    payload = {
        "model": "claude-3-haiku-20240307",  # Using haiku for better reliability
        "max_tokens": 1000,
        "temperature": 0.3,
        "messages": messages
    }
    
    # Make the API request
    logger.debug(f"Sending request to Claude API with {len(messages)} messages")
    response = requests.post(api_url, json=payload, headers=headers)
    
    # Check for errors
    if response.status_code != 200:
        logger.error(f"Claude API error: {response.status_code} - {response.text}")
        raise Exception(f"Error from Claude API: {response.status_code}")
    
    # Parse the response
    result = response.json()
    if 'content' in result and len(result['content']) > 0:
        chat_response = result['content'][0]['text'].strip()
        logger.info("Successfully generated chat response")
        return chat_response
    else:
        logger.error("Invalid response format from Claude API")
        raise ValueError("Failed to extract response from API result")

def get_document_chat_fallback(document_text, user_question, chat_history, api_key):
    """Generate a fallback response when Claude API is unavailable"""
    # Extract document title or name for context
    doc_lines = document_text.split('\n')
    doc_title = "this document"
    if doc_lines and doc_lines[0].strip():
        doc_title = f'"{doc_lines[0].strip()}"'
    
    return f"""I'm currently having trouble accessing my knowledge base to process your question about {doc_title}. 

Here are some general suggestions:
1. Try asking a simpler or more specific question
2. Try rephrasing your question 
3. Try again in a few minutes as this may be a temporary connection issue

If you're looking for specific information from the document, you might want to try scanning the document yourself for relevant sections related to "{user_question}"."""