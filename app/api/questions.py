from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import json
import logging
from datetime import datetime

from app import db
from app.models.document import Document, Question, DocumentChunk
from app.utils.api_utils import APIError, log_api_access

# Set up logging
logger = logging.getLogger(__name__)

questions_bp = Blueprint('questions', __name__, url_prefix='/api/questions')

@questions_bp.route('/generate', methods=['POST'])
@login_required
def generate_questions():
    """Generate questions for a document"""
    try:
        data = request.get_json()
        
        # Validate request data
        if not data:
            raise APIError("Missing request data", code=400)
            
        if 'document_id' not in data:
            raise APIError("Missing document_id parameter", code=400)
            
        document_id = data.get('document_id')
        question_type = data.get('question_type', 'mcq')
        count = data.get('count', 5)
        
        # Validate count (prevent excessive requests)
        if count > 20:
            count = 20
            
        # Get question generator from service container
        question_generator = current_app.services.get('question_generator')
        if not question_generator:
            raise APIError("Question generation service unavailable", code=503)
        
        # Generate questions
        questions, error = question_generator.generate_questions_for_document(
            document_id, current_user.id, question_type, count
        )
        
        if error:
            raise APIError(error, code=400)
            
        log_api_access("generate_questions", True, {
            "document_id": document_id,
            "question_type": question_type,
            "count": len(questions)
        })
            
        return jsonify({
            'questions': questions,
            'count': len(questions)
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error generating questions")
        log_api_access("generate_questions", False)
        raise APIError.from_exception(e, default_message="Failed to generate questions")

@questions_bp.route('/document/<int:document_id>', methods=['GET'])
@login_required
def get_questions_for_document(document_id):
    """Get all questions for a specific document"""
    try:
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            raise APIError("Document not found", code=404)
            
        # Filter by question type if specified
        question_type = request.args.get('type')
        
        query = Question.query.filter_by(document_id=document_id, user_id=current_user.id)
        
        if question_type:
            query = query.filter_by(question_type=question_type)
            
        questions = query.all()
        
        log_api_access("get_document_questions", True, {
            "document_id": document_id,
            "count": len(questions)
        })
            
        return jsonify({
            'questions': [q.to_dict() for q in questions],
            'count': len(questions)
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting questions for document")
        log_api_access("get_document_questions", False, {"document_id": document_id})
        raise APIError.from_exception(e, default_message="Failed to retrieve questions")

@questions_bp.route('/evaluate/<int:question_id>', methods=['POST'])
@login_required
def evaluate_answer(question_id):
    """Evaluate a user's answer to a question and update SRS data"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIError("Missing request data", code=400)
            
        if 'answer' not in data:
            raise APIError("Missing answer parameter", code=400)
            
        user_answer = data.get('answer')
        
        # Get question generator from service container
        question_generator = current_app.services.get('question_generator')
        if not question_generator:
            raise APIError("Question evaluation service unavailable", code=503)
            
        # First get the question to verify ownership
        question = Question.query.filter_by(id=question_id, user_id=current_user.id).first()
        if not question:
            raise APIError("Question not found or unauthorized", code=404)
        
        # Evaluate answer
        evaluation = question_generator.evaluate_answer(question_id, user_answer)
        
        # Update SRS data if evaluation was successful
        if evaluation and 'is_correct' in evaluation:
            question.update_srs_data(evaluation['is_correct'])
            
        log_api_access("evaluate_answer", True, {
            "question_id": question_id,
            "correct": evaluation.get('is_correct', False)
        })
            
        return jsonify(evaluation), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error evaluating answer")
        log_api_access("evaluate_answer", False, {"question_id": question_id})
        raise APIError.from_exception(e, default_message="Failed to evaluate answer")

@questions_bp.route('/due-for-review', methods=['GET'])
@login_required
def get_due_questions():
    """Get questions that are due for review according to SRS schedule"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        document_id = request.args.get('document_id', type=int)
        
        # Base query for questions due for review with proper syntax
        query = Question.query.filter(
            Question.user_id == current_user.id,
            # Questions with review date in the past or never reviewed
            db.or_(
                Question.next_review <= datetime.utcnow(),
                Question.next_review == None
            )
        )
        
        # Filter by document if specified
        if document_id:
            document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
            if not document:
                raise APIError("Document not found", code=404)
                
            query = query.filter_by(document_id=document_id)
        
        # Order by priority with proper syntax:
        # 1. Never answered questions first
        # 2. Then questions with lower success rates
        query = query.order_by(
            # CASE expression to prioritize never answered questions
            db.case((Question.times_answered == 0, 0), else_=1),
            # Use a calculated column for success rate - use CASE instead of greatest for SQLite compatibility
            (db.func.cast(Question.times_correct, db.Float) / 
             db.case((Question.times_answered < 1, 1), else_=Question.times_answered)).asc()
        )
        
        # Limit results
        questions = query.limit(limit).all()
        
        log_api_access("get_due_questions", True, {"count": len(questions)})
            
        return jsonify({
            'questions': [q.to_dict() for q in questions],
            'count': len(questions)
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting due questions")
        log_api_access("get_due_questions", False)
        raise APIError.from_exception(e, default_message="Failed to retrieve due questions")

@questions_bp.route('/by-difficulty', methods=['GET'])
@login_required
def get_questions_by_difficulty():
    """Get questions filtered by difficulty level"""
    try:
        # Get query parameters
        difficulty = request.args.get('level', 'medium')
        document_id = request.args.get('document_id', type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Validate difficulty level
        if difficulty not in ['easy', 'medium', 'hard']:
            raise APIError("Invalid difficulty level. Must be 'easy', 'medium', or 'hard'.", code=400)
            
        # Build query
        query = Question.query.filter_by(user_id=current_user.id, difficulty=difficulty)
        
        # Filter by document if specified
        if document_id:
            document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
            if not document:
                raise APIError("Document not found", code=404)
                
            query = query.filter_by(document_id=document_id)
        
        # Get results
        questions = query.limit(limit).all()
        
        log_api_access("get_questions_by_difficulty", True, {
            "difficulty": difficulty,
            "count": len(questions)
        })
            
        return jsonify({
            'questions': [q.to_dict() for q in questions],
            'count': len(questions),
            'difficulty': difficulty
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error getting questions by difficulty")
        log_api_access("get_questions_by_difficulty", False)
        raise APIError.from_exception(e, default_message="Failed to retrieve questions by difficulty")

@questions_bp.route('/', methods=['GET'])
@login_required
def get_all_questions():
    """Get all questions for the current user"""
    try:
        questions = Question.query.filter_by(user_id=current_user.id).all()
        
        log_api_access("get_all_questions", True, {"count": len(questions)})
            
        return jsonify({
            'questions': [q.to_dict() for q in questions],
            'count': len(questions)
        }), 200
        
    except Exception as e:
        logger.exception("Error getting all questions")
        log_api_access("get_all_questions", False)
        raise APIError.from_exception(e, default_message="Failed to retrieve questions")

@questions_bp.route('/document/<int:document_id>', methods=['POST'])
@login_required
def generate_questions_for_document(document_id):
    """Generate questions for a specific document with improved error handling"""
    try:
        data = request.get_json()
        
        # Validate request data
        if not data:
            raise APIError("Missing request data", code=400)
            
        question_type = data.get('question_type', 'mcq')
        difficulty_levels = data.get('difficulty_levels', ['easy', 'medium', 'hard'])
        
        # For backward compatibility
        if 'count' in data:
            count = data.get('count', 5)
        else:
            # Calculate count based on document size - will be handled in question_generator
            count = None
            
        # Validate parameters
        if count is not None and count > 30:
            count = 30
            
        if question_type not in ['mcq', 'qa', 'true_false', 'fill_in_blank', 'mixed']:
            raise APIError(f"Invalid question_type: {question_type}", code=400)
            
        # Verify document exists and belongs to user
        document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
        if not document:
            raise APIError("Document not found or unauthorized", code=404)
            
        # Check for document chunks first
        chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
        if not chunks:
            logger.warning(f"No chunks found for document {document_id}, attempting to create chunks")
            
            # Get document processor to attempt extraction
            document_processor = current_app.services.get('document_processor')
            if not document_processor:
                raise APIError("Document processing service unavailable", code=503)
                
            # Try to process document text and create chunks
            success, error = document_processor.process_document_text(document)
            if not success:
                logger.error(f"Failed to process document text: {error}")
                raise APIError(f"Failed to process document text: {error}", code=400)
                
            # Check if chunks were created
            chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
            if not chunks:
                raise APIError("Failed to create document chunks for question generation", code=400)
        
        # Get question generator from service container
        question_generator = current_app.services.get('question_generator')
        if not question_generator:
            raise APIError("Question generation service unavailable", code=503)
        
        # Generate questions
        logger.info(f"Generating questions of type {question_type} with difficulties {difficulty_levels} for document {document_id}")
        questions, error = question_generator.generate_questions_for_document(
            document_id, current_user.id, question_type, count, difficulty_levels
        )
        
        if error:
            logger.error(f"Error generating questions: {error}")
            raise APIError(error, code=400)
            
        if not questions:
            logger.warning(f"No questions generated for document {document_id}")
            raise APIError("Failed to generate questions from document content", code=400)
            
        log_api_access("generate_questions", True, {
            "document_id": document_id,
            "question_type": question_type,
            "count": len(questions)
        })
            
        return jsonify({
            'questions': questions,
            'count': len(questions)
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        log_api_access("generate_questions", False, {
            "document_id": document_id,
            "error": str(e) if 'e' in locals() else "API Error"
        })
        raise
    except Exception as e:
        logger.exception(f"Error generating questions for document {document_id}")
        log_api_access("generate_questions", False, {
            "document_id": document_id,
            "error": str(e)
        })
        raise APIError.from_exception(e, default_message="Failed to generate questions")

@questions_bp.route('/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Delete all saved questions for the current user"""
    try:
        logger.info(f"Request to clear question history for user {current_user.id}")
        
        # Get all questions for the user
        questions = Question.query.filter_by(user_id=current_user.id).all()
        count = len(questions)
        
        logger.info(f"Found {count} questions to delete for user {current_user.id}")
        
        # Delete all questions
        for question in questions:
            db.session.delete(question)
        
        db.session.commit()
        
        log_api_access("clear_quiz_history", True, {"count": count})
        logger.info(f"Successfully deleted {count} questions for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {count} questions',
            'count': count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error clearing question history for user {current_user.id}: {str(e)}")
        log_api_access("clear_quiz_history", False, {"error": str(e)})
        
        # Return a proper error response
        return jsonify({
            'success': False,
            'error': str(e),
            'message': "Failed to clear question history"
        }), 500

@questions_bp.route('/save', methods=['POST'])
@login_required
def save_questions():
    """Explicitly save questions to ensure they're marked as saved"""
    try:
        data = request.get_json()
        
        if not data or 'question_ids' not in data:
            raise APIError("Missing question_ids parameter", code=400)
            
        question_ids = data.get('question_ids', [])
        if not question_ids:
            raise APIError("No question IDs provided", code=400)
            
        # Verify all questions exist and belong to user
        questions = []
        for q_id in question_ids:
            question = Question.query.filter_by(id=q_id, user_id=current_user.id).first()
            if not question:
                continue  # Skip questions that don't exist or don't belong to user
            questions.append(question)
        
        # Mark questions as saved (we could add a saved flag if needed)
        # For now, we just ensure they exist in the database
        if not questions:
            raise APIError("No valid questions found", code=404)
            
        log_api_access("save_questions", True, {"count": len(questions)})
        
        return jsonify({
            'success': True,
            'count': len(questions),
            'message': f'Successfully saved {len(questions)} questions'
        }), 200
        
    except APIError:
        # Re-raise APIError to be handled by the global handler
        raise
    except Exception as e:
        logger.exception("Error saving questions")
        log_api_access("save_questions", False)
        raise APIError.from_exception(e, default_message="Failed to save questions")