from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.user import User

auth_routes_bp = Blueprint('auth_views', __name__)

@auth_routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth_views.login'))
        
        # Login user
        login_user(user, remember=remember)
        user.update_last_login()
        
        # Redirect to requested page or home
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.index'))
    
    # Handle GET request (show login page)
    return render_template('auth/login.html')

@auth_routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('auth_views.register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth_views.register'))
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | 
            (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                flash('Username already exists', 'danger')
            else:
                flash('Email already exists', 'danger')
            return redirect(url_for('auth_views.register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('auth_views.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
            return redirect(url_for('auth_views.register'))
    
    # Handle GET request (show register page)
    return render_template('auth/register.html')

@auth_routes_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth_routes_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

@auth_routes_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if email and email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists', 'danger')
                return redirect(url_for('auth_views.edit_profile'))
            
            current_user.email = email
        
        # Change password if provided
        if new_password:
            if not current_password:
                flash('Current password is required', 'danger')
                return redirect(url_for('auth_views.edit_profile'))
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('auth_views.edit_profile'))
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('auth_views.edit_profile'))
            
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth_views.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('auth_views.edit_profile'))
    
    return render_template('auth/edit_profile.html')