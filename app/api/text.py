from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.services.text_processor import TextProcessor

text_bp = Blueprint('text', __name__, url_prefix='/api/text')

# Initialize services
@text_bp.before_request
def setup_services():
    if not hasattr(text_bp, 'text_processor'):
        text_bp.text_processor = TextProcessor(
            api_key=current_app.config['ANTHROPIC_API_KEY']
        )

@text_bp.route('/summarize', methods=['POST'])
@login_required
def summarize_text():
    """Summarize text"""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'error': 'No text provided'}), 400
    
    # Get parameters
    text = data.get('text')
    length = data.get('length', 'medium')  # short, medium, or long
    format = data.get('format', 'paragraph')  # paragraph or bullets
    
    # Validate parameters
    if length not in ['short', 'medium', 'long']:
        return jsonify({'error': 'Invalid length, must be "short", "medium", or "long"'}), 400
    
    if format not in ['paragraph', 'bullets']:
        return jsonify({'error': 'Invalid format, must be "paragraph" or "bullets"'}), 400
    
    # Summarize the text
    summary, error = text_bp.text_processor.summarize(
        text=text,
        length=length,
        format=format
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'summary': summary,
        'original_length': len(text),
        'summary_length': len(summary)
    }), 200

@text_bp.route('/correct', methods=['POST'])
@login_required
def correct_text():
    """Correct grammar and improve clarity of text"""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'error': 'No text provided'}), 400
    
    # Correct the text
    corrected, error, corrections = text_bp.text_processor.correct_text(data.get('text'))
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'corrected_text': corrected,
        'original_text': data.get('text'),
        'corrections': corrections or []
    }), 200

@text_bp.route('/rephrase', methods=['POST'])
@login_required
def rephrase_text():
    """Rephrase text in a different style"""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'error': 'No text provided'}), 400
    
    # Get parameters
    text = data.get('text')
    style = data.get('style', 'academic')  # academic, simple, creative, professional
    
    # Validate parameters
    if style not in ['academic', 'simple', 'creative', 'professional']:
        return jsonify({'error': 'Invalid style, must be "academic", "simple", "creative", or "professional"'}), 400
    
    # Rephrase the text
    rephrased, error = text_bp.text_processor.rephrase_text(
        text=text,
        style=style
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'rephrased_text': rephrased,
        'original_text': text,
        'style': style
    }), 200

@text_bp.route('/explain', methods=['POST'])
@login_required
def explain_text():
    """Explain complex text in simpler terms"""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'error': 'No text provided'}), 400
    
    # Get parameters
    text = data.get('text')
    level = data.get('level', 'high_school')  # elementary, middle_school, high_school, college
    
    # Validate parameters
    if level not in ['elementary', 'middle_school', 'high_school', 'college']:
        return jsonify({'error': 'Invalid level, must be "elementary", "middle_school", "high_school", or "college"'}), 400
    
    # Explain the text
    explanation, error = text_bp.text_processor.explain_text(
        text=text,
        level=level
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'explanation': explanation,
        'original_text': text,
        'level': level
    }), 200