from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models.document import Document, Question
from app.services.question_generator import QuestionGenerator

questions_bp = Blueprint('questions', __name__, url_prefix='/api/questions')

# Initialize services
@questions_bp.before_request
def setup_services():
    if not hasattr(questions_bp, 'question_generator'):
        questions_bp.question_generator = QuestionGenerator(
            api_key=current_app.config['ANTHROPIC_API_KEY']
        )

@questions_bp.route('/document/<int:document_id>', methods=['POST'])
@login_required
def generate_questions(document_id):
    """Generate questions from a document"""
    data = request.get_json() or {}
    
    # Check if document exists and belongs to user
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    # Get parameters for question generation
    question_type = data.get('question_type', 'mcq')  # Default to multiple choice
    count = data.get('count', 5)  # Default to 5 questions
    
    # Validate parameters
    valid_question_types = ['mcq', 'qa', 'true_false', 'fill_in_blank']
    if question_type not in valid_question_types:
        return jsonify({'error': f'Invalid question type, must be one of: {", ".join(valid_question_types)}'}), 400
    
    if not isinstance(count, int) or count < 1 or count > 20:
        return jsonify({'error': 'Count must be between 1 and 20'}), 400
    
    # Generate questions
    questions, error = questions_bp.question_generator.generate_questions_for_document(
        document_id=document_id,
        user_id=current_user.id,
        question_type=question_type,
        count=count
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'questions': questions,
        'document_id': document_id,
        'question_type': question_type
    }), 200

@questions_bp.route('/', methods=['GET'])
@login_required
def get_all_questions():
    """Get all questions for the current user"""
    questions = Question.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'questions': [q.to_dict() for q in questions]
    }), 200

@questions_bp.route('/document/<int:document_id>', methods=['GET'])
@login_required
def get_questions_for_document(document_id):
    """Get questions for a specific document"""
    # Check if document exists and belongs to user
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    questions = Question.query.filter_by(document_id=document_id, user_id=current_user.id).all()
    return jsonify({
        'questions': [q.to_dict() for q in questions],
        'document_id': document_id
    }), 200

@questions_bp.route('/<int:question_id>', methods=['GET'])
@login_required
def get_question(question_id):
    """Get a specific question"""
    question = Question.query.filter_by(id=question_id, user_id=current_user.id).first()
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    return jsonify(question.to_dict()), 200

@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.filter_by(id=question_id, user_id=current_user.id).first()
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    try:
        db.session.delete(question)
        db.session.commit()
        return jsonify({
            'message': 'Question deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@questions_bp.route('/<int:question_id>/evaluate', methods=['POST'])
@login_required
def evaluate_answer(question_id):
    """Evaluate an answer to a question"""
    data = request.get_json()
    
    if not data or 'answer' not in data:
        return jsonify({'error': 'No answer provided'}), 400
    
    # Check if question exists and belongs to user
    question = Question.query.filter_by(id=question_id, user_id=current_user.id).first()
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    # Evaluate the answer
    evaluation = questions_bp.question_generator.evaluate_answer(
        question_id=question_id,
        user_answer=data.get('answer')
    )
    
    if 'error' in evaluation:
        return jsonify({'error': evaluation['error']}), 400
    
    return jsonify(evaluation), 200