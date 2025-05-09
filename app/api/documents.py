# app/api/documents.py - Redesigned Documents API

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import os
import json
import logging
import uuid
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
import time
import zipfile
import re
import requests
import tempfile
import mimetypes
from pathlib import Path

from app import db
from app.models.document import Document
from app.models.chat import ChatHistory
from app.utils.api_utils import APIError, log_api_access
from app.utils.claude import get_anthropic_client
from app.utils.summarize import generate_summary
from app.services.document_processor import DocumentProcessor

# Set up logging
logger = logging.getLogger(__name__)

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/', methods=['GET'])
@login_required
def get_documents():
    """Get all documents for the current user"""
    try:
        documents = Document.query.filter_by(user_id=current_user.id).all()
        log_api_access("get_documents", True, {"count": len(documents)})
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
    except Exception as e:
        logger.exception("Error getting documents")
        log_api_access("get_documents", False)
        raise APIError.from_exception(e, default_message="Failed to retrieve documents")

@documents_bp.route('/<int:document_id>', methods=['GET'])
@login_required
def get_document(document_id):
    """Get a specific document"""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        log_api_access("get_document", False, {"document_id": document_id})
        raise APIError("Document not found", code=404)
    
    log_api_access("get_document", True, {"document_id": document_id})
    return jsonify(document.to_dict()), 200

@documents_bp.route('/', methods=['POST'])
@login_required
def upload_document():
    """Upload a new document"""
    try:
        # Check if file is present in the request
        if 'file' not in request.files:
            raise APIError("No file part", code=400)
        
        file = request.files['file']
        if file.filename == '':
            raise APIError("No selected file", code=400)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
        
        # Save the file and create document record
        document, error = document_processor.save_file(file, current_user.id)
        if error:
            log_api_access("upload_document", False, {"error": error})
            raise APIError(error, code=400)
        
        # Return success response
        log_api_access("upload_document", True, {
            "document_id": document.id,
            "file_type": document.file_type,
            "file_size": document.file_size
        })
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': document.to_dict()
        }), 201
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error uploading document")
        log_api_access("upload_document", False)
        raise APIError.from_exception(e, default_message="Failed to upload document")

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    """Delete a document"""
    try:
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
        
        success, error = document_processor.delete_document(document_id, current_user.id)
        
        if not success:
            log_api_access("delete_document", False, {"document_id": document_id, "error": error})
            raise APIError(error, code=400)
        
        log_api_access("delete_document", True, {"document_id": document_id})
        return jsonify({
            'message': 'Document deleted successfully'
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error deleting document")
        log_api_access("delete_document", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to delete document")

@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@login_required
def download_document(document_id):
    """Download the original document"""
    try:
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            log_api_access("download_document", False, {"document_id": document_id})
            raise APIError("Document not found", code=404)
        
        # Update last accessed
        document.update_last_accessed()
        
        log_api_access("download_document", True, {"document_id": document_id})
        # Send the file
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error downloading document")
        log_api_access("download_document", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to download document")

@documents_bp.route('/<int:document_id>/text', methods=['GET'])
@login_required
def get_document_text(document_id):
    """Get the text content of a document"""
    try:
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
            
        text, error = document_processor.get_document_text(document_id)
        
        if error:
            log_api_access("get_document_text", False, {"document_id": document_id, "error": error})
            raise APIError(error, code=400)
        
        log_api_access("get_document_text", True, {"document_id": document_id})
        return jsonify({
            'text': text
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting document text")
        log_api_access("get_document_text", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to get document text")

@documents_bp.route('/<int:document_id>/summarize', methods=['GET'])
@login_required
def summarize_document(document_id):
    """Generate a summary of a document using Claude API"""
    try:
        # Check if document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            log_api_access("summarize_document", False, {"document_id": document_id})
            raise APIError("Document not found", code=404)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
            
        # Generate summary
        summary, error = document_processor.summarize_document(document_id)
        
        if error:
            log_api_access("summarize_document", False, {"document_id": document_id, "error": error})
            raise APIError(error, code=400)
        
        log_api_access("summarize_document", True, {"document_id": document_id})
        return jsonify({
            'summary': summary,
            'document_id': document_id,
            'document_name': document.original_filename
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error summarizing document")
        log_api_access("summarize_document", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to summarize document")

@documents_bp.route('/process-image', methods=['POST'])
@login_required
def process_image():
    """Process an image with OCR and optional AI analysis"""
    try:
        # Check if image is in the request
        if 'image' not in request.files:
            raise APIError("No image file provided", code=400)
        
        image = request.files['image']
        if image.filename == '':
            raise APIError("No selected image", code=400)
        
        # Check file type
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            raise APIError("Invalid image format. Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF", code=400)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
        
        # Generate a secure filename and save temporarily
        filename = secure_filename(image.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        image.save(temp_path)
        logger.info(f"Saved image temporarily to {temp_path}")
        
        # Extract text with OCR
        extracted_text = document_processor.extract_text_from_image(temp_path)
        
        # Analyze with AI if requested
        analyze = request.form.get('analyze', 'false').lower() == 'true'
        analysis = None
        
        if analyze:
            logger.info("Analyzing image content with AI")
            analysis = document_processor.analyze_image_content(temp_path)
        
        # Option to save as document
        save_as_document = request.form.get('save', 'false').lower() == 'true'
        document_id = None
        
        if save_as_document:
            # Create document record
            document = Document(
                filename=unique_filename,
                original_filename=filename,
                file_type='image',
                file_size=os.path.getsize(temp_path),
                file_path=temp_path,
                user_id=current_user.id
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Create a chunk for the extracted text
            if extracted_text:
                chunk = DocumentChunk(
                    chunk_text=extracted_text,
                    chunk_index=0,
                    document_id=document.id
                )
                db.session.add(chunk)
                db.session.commit()
            
            document_id = document.id
            logger.info(f"Saved image as document with ID {document_id}")
        else:
            # Clean up temp file if not saving
            try:
                os.remove(temp_path)
                logger.info(f"Removed temporary file {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {str(e)}")
        
        # Log successful processing
        log_api_access("process_image", True, {
            "has_text": bool(extracted_text),
            "analyzed": analyze,
            "saved": save_as_document
        })
        
        # Return the extracted information
        result = {
            'text': extracted_text,
            'success': True
        }
        
        if analysis:
            result['analysis'] = analysis
            
        if document_id:
            result['document_id'] = document_id
            
        return jsonify(result), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error processing image")
        log_api_access("process_image", False)
        raise APIError.from_exception(e, default_message="Failed to process image")

@documents_bp.route('/<int:document_id>/process-with-ocr', methods=['POST'])
@login_required
def process_document_with_ocr(document_id):
    """Process a document with OCR for image-based content"""
    try:
        # Check if document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            log_api_access("process_document_with_ocr", False, {"document_id": document_id})
            raise APIError("Document not found", code=404)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
        
        # Process the document with OCR
        success, error = document_processor.process_document_with_images(document_id)
        
        if not success:
            log_api_access("process_document_with_ocr", False, {"document_id": document_id, "error": error})
            raise APIError(error, code=400)
        
        log_api_access("process_document_with_ocr", True, {"document_id": document_id})
        return jsonify({
            'message': 'Document processed successfully with OCR',
            'document_id': document_id
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error processing document with OCR")
        log_api_access("process_document_with_ocr", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to process document with OCR")

@documents_bp.route('/ocr', methods=['POST'])
@login_required
def process_image_ocr():
    """Process an image with OCR and return the extracted text"""
    try:
        # Check if file is present in the request
        if 'image' not in request.files:
            raise APIError("No image part", code=400)
        
        image_file = request.files['image']
        if image_file.filename == '':
            raise APIError("No selected image", code=400)
        
        # Check file extension
        allowed_extensions = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
        file_ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise APIError(f"File type not allowed. Supported formats: {', '.join(allowed_extensions)}", code=400)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("OCR processing service unavailable", code=503)
        
        # Process the image with OCR
        image_data = image_file.read()
        
        # Use Hugging Face OCR model or Claude Vision
        text = current_app.services.get('ai_service').process_image_ocr(image_data)
        
        if not text:
            raise APIError("Failed to extract text from image", code=400)
        
        log_api_access("process_image_ocr", True, {"image_size": len(image_data)})
        
        return jsonify({
            'text': text,
            'file_name': image_file.filename
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error processing OCR image")
        log_api_access("process_image_ocr", False)
        raise APIError.from_exception(e, default_message="Failed to process image")

@documents_bp.route('/summarize', methods=['POST'])
@login_required
def summarize_document_post():
    """Generate a summary for a document"""
    try:
        data = request.get_json()
        
        if not data or 'document_id' not in data:
            raise APIError("Missing document_id parameter", code=400)
            
        document_id = data.get('document_id')
        
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            raise APIError("Document not found", code=404)
            
        # Get document text
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
            
        text = document_processor._extract_document_text(document)
        
        if not text or len(text) < 10:
            raise APIError("Document has insufficient text to summarize", code=400)
            
        # Get Claude service for summarization
        claude_service = current_app.services.get('ai_service')
        if not claude_service:
            raise APIError("AI service unavailable", code=503)
            
        # Generate summary
        summary = claude_service.summarize_text(text)
        
        if not summary:
            raise APIError("Failed to generate summary", code=500)
            
        # Record API access
        log_api_access("summarize_document", True, {"document_id": document_id})
        
        return jsonify({
            'summary': summary,
            'document_id': document_id
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error summarizing document")
        log_api_access("summarize_document", False, {"document_id": data.get('document_id') if data else None})
        raise APIError.from_exception(e, default_message="Failed to summarize document")

@documents_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_document():
    """Chat with a document using Claude API"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("Missing request data", code=400)
            
        if 'document_id' not in data or 'query' not in data:
            raise APIError("Missing required parameters (document_id, query)", code=400)
            
        document_id = data.get('document_id')
        question = data.get('query')
        chat_history = data.get('chat_history', [])
        session_id = data.get('session_id')
        
        # If no session_id provided, create a new one
        if not session_id:
            session_id = f"doc_{document_id}_{uuid.uuid4().hex[:8]}"
        
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
        
        # Save question and answer to chat history
        ChatHistory.save_message(
            user_id=current_user.id,
            role='user',
            message=question,
            document_id=document_id,
            session_id=session_id
        )
        
        ChatHistory.save_message(
            user_id=current_user.id,
            role='assistant',
            message=answer,
            document_id=document_id,
            session_id=session_id
        )
            
        log_api_access("chat_with_document", True, {
            "document_id": document_id,
            "question_length": len(question),
            "session_id": session_id
        })
            
        return jsonify({
            'response': answer,  # Used "response" to match what the frontend expects
            'document_id': document_id,
            'session_id': session_id,
            'is_fallback': False
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

@documents_bp.route('/<int:document_id>/content', methods=['GET'])
@login_required
def get_document_content(document_id):
    """Get the full content of a document"""
    try:
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            log_api_access("get_document_content", False, {"document_id": document_id})
            raise APIError("Document not found", code=404)
        
        # Get document processor from service container
        document_processor = current_app.services.get('document_processor')
        if not document_processor:
            raise APIError("Document processing service unavailable", code=503)
            
        # Get the document text
        text, error = document_processor.get_document_text(document_id)
        
        if error:
            log_api_access("get_document_content", False, {"document_id": document_id, "error": error})
            raise APIError(error, code=400)
        
        # Update last accessed
        document.update_last_accessed()
        
        log_api_access("get_document_content", True, {"document_id": document_id})
        return jsonify({
            'text': text,
            'document_id': document_id,
            'document_name': document.original_filename
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting document content")
        log_api_access("get_document_content", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to get document content")

@documents_bp.route('/<int:document_id>/chat-history', methods=['GET'])
@login_required
def get_document_chat_history(document_id):
    """Get chat history for a document"""
    try:
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            log_api_access("get_document_chat_history", False, {"document_id": document_id})
            raise APIError("Document not found", code=404)
        
        # Get chat sessions for the document
        chat_sessions = ChatHistory.get_chat_sessions(current_user.id, document_id)
        
        if not chat_sessions:
            return jsonify({
                'sessions': []
            }), 200
        
        # Format sessions for the response
        sessions = []
        for session in chat_sessions:
            sessions.append({
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                'message_count': session.message_count
            })
        
        log_api_access("get_document_chat_history", True, {
            "document_id": document_id,
            "session_count": len(sessions)
        })
        
        return jsonify({
            'sessions': sessions
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting document chat history")
        log_api_access("get_document_chat_history", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to get document chat history")

@documents_bp.route('/chat-sessions/<string:session_id>', methods=['GET'])
@login_required
def get_chat_session(session_id):
    """Get messages for a specific chat session"""
    try:
        # Get chat messages for the session
        chat_messages = ChatHistory.get_chat_history(current_user.id, session_id=session_id)
        
        if not chat_messages:
            return jsonify({
                'messages': [],
                'session_id': session_id
            }), 200
        
        # Get document info if available
        document_id = chat_messages[0].document_id
        document = None
        if document_id:
            document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        
        # Format messages for the response
        messages = []
        for message in chat_messages:
            messages.append({
                'id': message.id,
                'role': message.role,
                'message': message.message,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None
            })
        
        log_api_access("get_chat_session", True, {
            "session_id": session_id,
            "message_count": len(messages)
        })
        
        response = {
            'messages': messages,
            'session_id': session_id
        }
        
        if document:
            response['document'] = {
                'id': document.id,
                'name': document.original_filename
            }
        
        return jsonify(response), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting chat session")
        log_api_access("get_chat_session", False, {"session_id": session_id})
        raise APIError.from_exception(e, default_message="Failed to get chat session")

@documents_bp.route('/chat-sessions', methods=['GET'])
@login_required
def get_all_chat_sessions():
    """Get all chat sessions for the current user"""
    try:
        # Get all chat sessions for the user
        chat_sessions = ChatHistory.get_chat_sessions(current_user.id)
        
        if not chat_sessions:
            return jsonify({
                'sessions': []
            }), 200
        
        # Get document info for sessions
        document_ids = set()
        for session in chat_sessions:
            # Get the document_id from one of the messages in the session
            chat_message = ChatHistory.query.filter_by(
                user_id=current_user.id, 
                session_id=session.session_id
            ).first()
            
            if chat_message and chat_message.document_id:
                document_ids.add(chat_message.document_id)
        
        documents = {}
        if document_ids:
            document_records = Document.query.filter(
                Document.id.in_(document_ids),
                Document.user_id == current_user.id
            ).all()
            
            for doc in document_records:
                documents[doc.id] = {
                    'id': doc.id,
                    'name': doc.original_filename
                }
        
        # Format sessions for the response
        sessions = []
        for session in chat_sessions:
            # Get document_id for this session
            chat_message = ChatHistory.query.filter_by(
                user_id=current_user.id, 
                session_id=session.session_id
            ).first()
            
            document_info = None
            if chat_message and chat_message.document_id and chat_message.document_id in documents:
                document_info = documents[chat_message.document_id]
            
            sessions.append({
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                'message_count': session.message_count,
                'document': document_info
            })
        
        log_api_access("get_all_chat_sessions", True, {
            "session_count": len(sessions)
        })
        
        return jsonify({
            'sessions': sessions
        }), 200
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting all chat sessions")
        log_api_access("get_all_chat_sessions", False)
        raise APIError.from_exception(e, default_message="Failed to get chat sessions")