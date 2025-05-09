from datetime import datetime
from app import db

class ChatHistory(db.Model):
    """Model for storing document chat history"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True, index=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)  # Unique ID for each chat session
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatHistory {self.id}: {self.role}>'
    
    def to_dict(self):
        """Convert chat history entry to dictionary"""
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'document_id': self.document_id,
            'session_id': self.session_id
        }
    
    @staticmethod
    def get_chat_history(user_id, document_id=None, session_id=None, limit=50):
        """Get chat history for a user/document/session"""
        query = ChatHistory.query.filter_by(user_id=user_id)
        
        if document_id:
            query = query.filter_by(document_id=document_id)
            
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        return query.order_by(ChatHistory.timestamp).limit(limit).all()
    
    @staticmethod
    def save_message(user_id, role, message, document_id=None, session_id=None):
        """Save a chat message"""
        if not session_id:
            session_id = f"session_{datetime.utcnow().timestamp()}"
            
        chat_entry = ChatHistory(
            user_id=user_id,
            role=role,
            message=message,
            document_id=document_id,
            session_id=session_id
        )
        
        db.session.add(chat_entry)
        db.session.commit()
        
        return chat_entry
    
    @staticmethod
    def get_chat_sessions(user_id, document_id=None):
        """Get list of distinct chat sessions for a user/document"""
        query = db.session.query(
            ChatHistory.session_id,
            db.func.min(ChatHistory.timestamp).label('start_time'),
            db.func.max(ChatHistory.timestamp).label('last_activity'),
            db.func.count(ChatHistory.id).label('message_count')
        ).filter_by(user_id=user_id)
        
        if document_id:
            query = query.filter_by(document_id=document_id)
            
        return query.group_by(ChatHistory.session_id)\
                   .order_by(db.desc('last_activity'))\
                   .all() 