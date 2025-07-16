from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    prompt = db.Column(db.Text)  # AI-generated writing prompt
    mood_before = db.Column(db.Integer)  # 1-5 mood before writing
    mood_after = db.Column(db.Integer)  # 1-5 mood after writing
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=True)
    tags = db.Column(db.String(255))  # Comma-separated tags
    word_count = db.Column(db.Integer, default=0)
    
    def __init__(self, user_id, content, title=None, prompt=None, mood_before=None, 
                 mood_after=None, tags=None, is_private=True):
        self.user_id = user_id
        self.content = content
        self.title = title
        self.prompt = prompt
        self.mood_before = mood_before
        self.mood_after = mood_after
        self.tags = tags
        self.is_private = is_private
        self.word_count = len(content.split()) if content else 0
    
    def update_word_count(self):
        """Update word count when content changes"""
        self.word_count = len(self.content.split()) if self.content else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'prompt': self.prompt,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_modified': self.date_modified.isoformat() if self.date_modified else None,
            'is_private': self.is_private,
            'tags': self.tags.split(',') if self.tags else [],
            'word_count': self.word_count
        }
    
    @property
    def mood_improvement(self):
        """Calculate mood improvement from before to after"""
        if self.mood_before and self.mood_after:
            return self.mood_after - self.mood_before
        return None
    
    def __repr__(self):
        return f'<JournalEntry {self.title or "Untitled"} - {self.date_created.date()}>'