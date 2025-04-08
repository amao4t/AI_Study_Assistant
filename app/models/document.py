from datetime import datetime
import os
import json
from app import db

class Document(db.Model):
    """Document model for storing uploaded files and their metadata"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, docx, txt
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    questions = db.relationship('Question', backref='document', lazy='dynamic')
    vector_chunks = db.relationship('DocumentChunk', backref='document', lazy='dynamic')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    def update_last_accessed(self):
        """Update the last accessed timestamp"""
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def get_file_extension(self):
        """Get the file extension"""
        return os.path.splitext(self.original_filename)[1][1:].lower()
    
    def to_dict(self):
        """Convert document to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }


class DocumentChunk(db.Model):
    """Model for storing document chunks for vector search"""
    id = db.Column(db.Integer, primary_key=True)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    embedding_stored = db.Column(db.Boolean, default=False)
    
    # Foreign keys
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    
    def __repr__(self):
        return f'<DocumentChunk {self.id} for Document {self.document_id}>'


class Question(db.Model):
    """Model for storing generated questions"""
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(15), nullable=False)  # mcq, qa, true_false, fill_in_blank
    options = db.Column(db.Text, nullable=True)  # JSON string for MCQ options
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Question {self.id}>'
    
    def to_dict(self):
        """Convert question to dictionary for API responses"""
        result = {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'answer': self.answer,
            'created_at': self.created_at.isoformat(),
            'document_id': self.document_id
        }
        
        # Parse options based on question type
        if self.options:
            try:
                result['options'] = json.loads(self.options)
            except:
                result['options'] = {}
                
        return result


class StudySession(db.Model):
    """Model for tracking study sessions"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    session_type = db.Column(db.String(20), nullable=False)  # qa, document_review, etc.
    notes = db.Column(db.Text, nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)
    
    def __repr__(self):
        return f'<StudySession {self.id}>'
    
    def end_session(self):
        """End the study session"""
        self.end_time = datetime.utcnow()
        db.session.commit()
    
    def calculate_duration(self):
        """Calculate the duration of the study session in minutes"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None