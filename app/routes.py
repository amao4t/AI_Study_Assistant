from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

# Create main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the homepage"""
    return render_template('index.html')

# Document routes
@main_bp.route('/documents')
@login_required
def documents_dashboard():
    """Render the documents dashboard"""
    return render_template('documents/dashboard.html')

# Questions routes
@main_bp.route('/questions')
@login_required
def questions_dashboard():
    """Render the questions dashboard"""
    return render_template('questions/dashboard.html')

# Text tools routes
@main_bp.route('/text')
@login_required
def text_dashboard():
    """Render the text tools dashboard"""
    return render_template('text/dashboard.html')

# Study assistant routes
@main_bp.route('/study')
@login_required
def study_dashboard():
    """Render the AI assistant dashboard"""
    return render_template('study/dashboard.html')

# OCR and Image processing routes
@main_bp.route('/ocr')
@login_required
def ocr_dashboard():
    """Render the OCR and image processing dashboard"""
    return render_template('ocr.html')