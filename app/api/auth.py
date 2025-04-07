from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime

from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    existing_user = User.query.filter(
        (User.username == data.get('username')) | 
        (User.email == data.get('email'))
    ).first()
    
    if existing_user:
        if existing_user.username == data.get('username'):
            return jsonify({'error': 'Username already exists'}), 400
        else:
            return jsonify({'error': 'Email already exists'}), 400
    
    # Create new user
    user = User(
        username=data.get('username'),
        email=data.get('email')
    )
    user.set_password(data.get('password'))
    
    # Save to database
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    # Find user by username
    user = User.query.filter_by(username=data.get('username')).first()
    
    # Check password
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Login user
    login_user(user)
    
    # Update last login time
    user.update_last_login()
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout a user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Check if email is being updated and if it already exists
    if data.get('email') and data.get('email') != current_user.email:
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        current_user.email = data.get('email')
    
    # Update password if provided
    if data.get('password'):
        current_user.set_password(data.get('password'))
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500