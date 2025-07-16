from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Mood(db.Model):
    __tablename__ = 'moods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 1-5 scale
    notes = db.Column(db.Text)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.String(255))  # Comma-separated tags like "stress,work,family"
    
    def __init__(self, user_id, score, notes=None, tags=None):
        self.user_id = user_id
        self.score = score
        self.notes = notes
        self.tags = tags
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'score': self.score,
            'notes': self.notes,
            'date_recorded': self.date_recorded.isoformat() if self.date_recorded else None,
            'tags': self.tags.split(',') if self.tags else []
        }
    
    @property
    def mood_label(self):
        """Convert numeric score to descriptive label"""
        labels = {
            1: "Very Low",
            2: "Low", 
            3: "Neutral",
            4: "Good",
            5: "Very Good"
        }
        return labels.get(self.score, "Unknown")
    
    def __repr__(self):
        return f'<Mood {self.score}/5 on {self.date_recorded.date()}>'