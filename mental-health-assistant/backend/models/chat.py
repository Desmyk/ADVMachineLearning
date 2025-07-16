from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    is_user_message = db.Column(db.Boolean, nullable=False)  # True for user, False for AI
    sentiment_score = db.Column(db.Float)  # VADER compound score
    sentiment_label = db.Column(db.String(20))  # positive, negative, neutral
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(36))  # UUID for grouping conversations
    
    def __init__(self, user_id, message, is_user_message=True, response=None, 
                 sentiment_score=None, sentiment_label=None, session_id=None):
        self.user_id = user_id
        self.message = message
        self.is_user_message = is_user_message
        self.response = response
        self.sentiment_score = sentiment_score
        self.sentiment_label = sentiment_label
        self.session_id = session_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'is_user_message': self.is_user_message,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }
    
    def __repr__(self):
        msg_type = "User" if self.is_user_message else "AI"
        return f'<ChatMessage {msg_type}: {self.message[:50]}...>'