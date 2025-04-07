# app/api/documents.py - Redesigned Documents API

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import os
import json

from app import db
from app.models.document import Document
from app.services.document_processor import DocumentProcessor

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

# Initialize document processor service
@documents_bp.before_request
def setup_services():
    if not hasattr(documents_bp, 'document_processor'):
        documents_bp.document_processor = DocumentProcessor(
            upload_folder=current_app.config['UPLOAD_FOLDER'],
            allowed_extensions=current_app.config['ALLOWED_EXTENSIONS']
        )

@documents_bp.route('/', methods=['GET'])
@login_required
def get_documents():
    """Get all documents for the current user"""
    documents = Document.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'documents': [doc.to_dict() for doc in documents]
    }), 200

@documents_bp.route('/<int:document_id>', methods=['GET'])
@login_required
def get_document(document_id):
    """Get a specific document"""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    return jsonify(document.to_dict()), 200

@documents_bp.route('/', methods=['POST'])
@login_required
def upload_document():
    """Upload a new document"""
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the file and create document record
    document, error = documents_bp.document_processor.save_file(file, current_user.id)
    if error:
        return jsonify({'error': error}), 400
    
    # Return success response
    return jsonify({
        'message': 'Document uploaded successfully',
        'document': document.to_dict()
    }), 201

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    """Delete a document"""
    success, error = documents_bp.document_processor.delete_document(document_id, current_user.id)
    
    if not success:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'Document deleted successfully'
    }), 200

@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@login_required
def download_document(document_id):
    """Download the original document"""
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Update last accessed
    document.update_last_accessed()
    
    # Send the file
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename
    )

@documents_bp.route('/<int:document_id>/text', methods=['GET'])
@login_required
def get_document_text(document_id):
    """Get the text content of a document"""
    text, error = documents_bp.document_processor.get_document_text(document_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'text': text
    }), 200

@documents_bp.route('/<int:document_id>/summarize', methods=['GET'])
@login_required
def summarize_document(document_id):
    """Generate a summary of a document using Claude API"""
    # Check if document exists and belongs to user
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Generate summary
    summary, error = documents_bp.document_processor.summarize_document(document_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'summary': summary,
        'document_id': document_id,
        'document_name': document.original_filename
    }), 200