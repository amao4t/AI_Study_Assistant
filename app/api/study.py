from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models.document import StudySession, StudyPlan
from app.services.study_assistant import StudyAssistant
from datetime import datetime
from sqlalchemy.sql import text

study_bp = Blueprint('study', __name__, url_prefix='/api/study')

# Initialize services
@study_bp.before_request
def setup_services():
    if not hasattr(study_bp, 'study_assistant'):
        study_bp.study_assistant = StudyAssistant(
            api_key=current_app.config['ANTHROPIC_API_KEY']
        )

@study_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Chat with the study assistant"""
    data = request.get_json()
    
    if not data or not data.get('message'):
        return jsonify({'error': 'No message provided'}), 400
    
    # Get chat history from the request
    chat_history = data.get('chat_history', [])
    
    # Chat with the assistant - now with fallback handling
    response, error, is_fallback = study_bp.study_assistant.chat(
        user_message=data.get('message'),
        chat_history=chat_history,
        use_fallback=True  # Enable fallback responses
    )
    
    if error and not is_fallback:
        # If there was an error and no fallback was generated
        return jsonify({'error': error}), 500
    
    # Update chat history with new message and response
    chat_history.append({'role': 'user', 'message': data.get('message')})
    chat_history.append({'role': 'assistant', 'message': response})
    
    return jsonify({
        'response': response,
        'chat_history': chat_history,
        'is_fallback': is_fallback  # Let the frontend know this is a fallback response
    }), 200

@study_bp.route('/plan', methods=['POST'])
@login_required
def generate_study_plan():
    """Generate a study plan"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get parameters
    subject = data.get('subject')
    goal = data.get('goal')
    timeframe = data.get('timeframe')
    hours_per_week = data.get('hours_per_week', 10)  # Default to 10 hours
    
    if not subject or not goal or not timeframe:
        return jsonify({'error': 'Missing required parameters (subject, goal, timeframe)'}), 400
    
    # Generate study plan
    study_plan, error = study_bp.study_assistant.generate_study_plan(
        subject=subject,
        goal=goal,
        timeframe=timeframe,
        hours_per_week=hours_per_week
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(study_plan), 200

@study_bp.route('/resources', methods=['POST'])
@login_required
def recommend_resources():
    """Recommend study resources"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get parameters
    subject = data.get('subject')
    level = data.get('level', 'undergraduate')  # Default to undergraduate
    resource_type = data.get('resource_type', 'all')  # Default to all types
    
    if not subject:
        return jsonify({'error': 'Missing required parameter (subject)'}), 400
    
    # Get resource recommendations
    resources, error = study_bp.study_assistant.recommend_resources(
        subject=subject,
        level=level,
        resource_type=resource_type
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'resources': resources,
        'subject': subject,
        'level': level
    }), 200

@study_bp.route('/techniques', methods=['POST'])
@login_required
def suggest_study_techniques():
    """Suggest study techniques"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get parameters
    subject = data.get('subject')
    learning_style = data.get('learning_style')
    
    if not subject:
        return jsonify({'error': 'Missing required parameter (subject)'}), 400
    
    # Get technique suggestions
    techniques, error = study_bp.study_assistant.suggest_study_technique(
        subject=subject,
        learning_style=learning_style
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'techniques': techniques,
        'subject': subject,
        'learning_style': learning_style
    }), 200

@study_bp.route('/session/start', methods=['POST'])
@login_required
def start_study_session():
    """Start a new study session"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get parameters
    session_type = data.get('session_type', 'general')
    document_id = data.get('document_id')  # Optional
    notes = data.get('notes')  # Optional
    
    # Create study session
    session = StudySession(
        session_type=session_type,
        notes=notes,
        user_id=current_user.id,
        document_id=document_id
    )
    
    try:
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Study session started',
            'session_id': session.id,
            'start_time': session.start_time.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@study_bp.route('/session/<int:session_id>/end', methods=['POST'])
@login_required
def end_study_session(session_id):
    """End a study session"""
    session = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({'error': 'Study session not found'}), 404
    
    if session.end_time:
        return jsonify({'error': 'Study session already ended'}), 400
    
    # Update notes if provided
    data = request.get_json() or {}
    if 'notes' in data:
        session.notes = data.get('notes')
    
    # End the session
    session.end_session()
    
    return jsonify({
        'message': 'Study session ended',
        'session_id': session.id,
        'duration_minutes': session.calculate_duration()
    }), 200

@study_bp.route('/sessions', methods=['GET'])
@login_required
def get_study_sessions():
    """Get all study sessions for the current user"""
    sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.start_time.desc()).all()
    
    return jsonify({
        'sessions': [{
            'id': session.id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration_minutes': session.calculate_duration(),
            'session_type': session.session_type,
            'document_id': session.document_id,
            'notes': session.notes
        } for session in sessions]
    }), 200

@study_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_study_session(session_id):
    """Delete a specific study session"""
    session = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({'error': 'Study session not found'}), 404
    
    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({'message': 'Study session deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@study_bp.route('/sessions/clear', methods=['DELETE'])
@login_required
def clear_all_sessions():
    """Delete all study sessions for the current user"""
    try:
        StudySession.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'message': 'All study sessions cleared successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@study_bp.route('/sessions/<int:session_id>/pause', methods=['POST'])
@login_required
def pause_study_session(session_id):
    """Pause a study session"""
    session = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({'error': 'Study session not found'}), 404
    
    if session.end_time:
        return jsonify({'error': 'Study session already ended'}), 400
    
    try:
        # For now, just mark it as paused (you might need to add a status field to your model)
        # This is a temporary solution - ideally you'd add a 'status' field to StudySession
        session.notes = (session.notes or '') + '\n[PAUSED]'
        db.session.commit()
        
        return jsonify({
            'message': 'Study session paused',
            'session_id': session.id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@study_bp.route('/sessions/<int:session_id>/resume', methods=['POST'])
@login_required
def resume_study_session(session_id):
    """Resume a paused study session"""
    session = StudySession.query.filter_by(id=session_id, user_id=current_user.id).first()
    
    if not session:
        return jsonify({'error': 'Study session not found'}), 404
    
    if session.end_time:
        return jsonify({'error': 'Study session already ended'}), 400
    
    try:
        # Remove the paused marker
        if session.notes and '[PAUSED]' in session.notes:
            session.notes = session.notes.replace('\n[PAUSED]', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Study session resumed',
            'session_id': session.id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ---- Study Plans API endpoints ----

@study_bp.route('/plans', methods=['GET'])
@login_required
def get_study_plans():
    """Get all saved study plans for current user"""
    try:
        plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.created_at.desc()).all()
        
        return jsonify({
            'plans': [plan.to_dict() for plan in plans]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching study plans: {str(e)}")
        return jsonify({'error': 'Failed to fetch study plans', 'details': str(e)}), 500

@study_bp.route('/plans', methods=['POST'])
@login_required
def save_study_plan():
    """Save a study plan"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get parameters
    subject = data.get('subject')
    overview = data.get('overview', '')
    weeks = data.get('weeks', '')
    techniques = data.get('techniques', '')
    milestones = data.get('milestones', '')
    
    if not subject:
        return jsonify({'error': 'Missing required parameter (subject)'}), 400
    
    try:
        # Create a new study plan object
        study_plan = StudyPlan(
            user_id=current_user.id,
            subject=subject,
            overview=overview,
            weeks=weeks,
            techniques=techniques,
            milestones=milestones
        )
        
        db.session.add(study_plan)
        db.session.commit()
        
        return jsonify({
            'message': 'Study plan saved successfully',
            'plan_id': study_plan.id,
            'created_at': study_plan.created_at.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving study plan: {str(e)}")
        return jsonify({'error': 'Failed to save study plan', 'details': str(e)}), 500

@study_bp.route('/plans/<int:plan_id>', methods=['GET'])
@login_required
def get_study_plan(plan_id):
    """Get a specific study plan"""
    try:
        plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
        
        if not plan:
            return jsonify({'error': 'Study plan not found'}), 404
        
        return jsonify(plan.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching study plan: {str(e)}")
        return jsonify({'error': 'Failed to fetch study plan', 'details': str(e)}), 500

@study_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_study_plan(plan_id):
    """Delete a specific study plan"""
    try:
        plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
        
        if not plan:
            return jsonify({'error': 'Study plan not found or not authorized to delete'}), 404
        
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'message': 'Study plan deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting study plan: {str(e)}")
        return jsonify({'error': 'Failed to delete study plan', 'details': str(e)}), 500

@study_bp.route('/plans/clear', methods=['DELETE'])
@login_required
def clear_all_plans():
    """Delete all study plans for the current user"""
    try:
        count = StudyPlan.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'message': 'All study plans cleared successfully', 'count': count}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error clearing study plans: {str(e)}")
        return jsonify({'error': 'Failed to clear study plans', 'details': str(e)}), 500