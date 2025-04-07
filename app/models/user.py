from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    documents = db.relationship('Document', backref='owner', lazy='dynamic')
    questions = db.relationship('Question', backref='creator', lazy='dynamic')
    study_sessions = db.relationship('StudySession', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash for user"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

@login_manager.user_loader
def load_user(id):
    """User loader for Flask-Login"""
    return User.query.get(int(id))