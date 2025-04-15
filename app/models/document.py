from datetime import datetime, timedelta
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
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
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, index=True)
    
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
    
    # SRS and difficulty fields
    difficulty = db.Column(db.String(10), default='medium')  # easy, medium, hard
    last_answered = db.Column(db.DateTime, nullable=True)
    times_answered = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    next_review = db.Column(db.DateTime, nullable=True)
    content_hash = db.Column(db.String(64), nullable=True)  # For caching
    
    # Foreign keys
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
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
            'document_id': self.document_id,
            'difficulty': self.difficulty,
            'times_answered': self.times_answered,
            'times_correct': self.times_correct,
            'next_review': self.next_review.isoformat() if self.next_review else None
        }
        
        # Parse options based on question type
        if self.options:
            try:
                result['options'] = json.loads(self.options)
            except:
                result['options'] = {}
                
        return result
    
    def update_srs_data(self, correct_answer):
        """Update SRS data based on answer correctness"""
        self.last_answered = datetime.utcnow()
        self.times_answered += 1
        
        if correct_answer:
            self.times_correct += 1
            
        # Calculate next review time based on performance
        success_rate = self.times_correct / max(1, self.times_answered)
        
        # Basic SRS algorithm - intervals expand with correct answers
        if success_rate >= 0.8:
            # User is doing well, longer interval
            days_until_review = min(30, self.times_correct)
        elif success_rate >= 0.5:
            # User is doing okay, medium interval
            days_until_review = 3
        else:
            # User needs more practice, short interval
            days_until_review = 1
            
        self.next_review = datetime.utcnow() + timedelta(days=days_until_review)
        db.session.commit()


class StudySession(db.Model):
    """Model for tracking study sessions"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    session_type = db.Column(db.String(20), nullable=False)  # qa, document_review, etc.
    notes = db.Column(db.Text, nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True, index=True)
    
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


class StudyPlan(db.Model):
    """Model for storing study plans"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    overview = db.Column(db.Text, nullable=True)
    weeks = db.Column(db.Text, nullable=True)
    techniques = db.Column(db.Text, nullable=True)
    milestones = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    def __repr__(self):
        return f'<StudyPlan {self.id}: {self.subject}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'subject': self.subject,
            'overview': self.overview,
            'weeks': self.weeks,
            'techniques': self.techniques,
            'milestones': self.milestones,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }