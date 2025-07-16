from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(512), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # 'video', 'article', 'guide', 'tool'
    category = db.Column(db.String(100))  # 'anxiety', 'depression', 'stress', 'mindfulness', etc.
    tags = db.Column(db.String(255))  # Comma-separated tags
    difficulty_level = db.Column(db.String(20))  # 'beginner', 'intermediate', 'advanced'
    estimated_duration = db.Column(db.Integer)  # Duration in minutes
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    views_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)  # Average user rating
    
    def __init__(self, title, url, resource_type, description=None, category=None, 
                 tags=None, difficulty_level='beginner', estimated_duration=None):
        self.title = title
        self.url = url
        self.resource_type = resource_type
        self.description = description
        self.category = category
        self.tags = tags
        self.difficulty_level = difficulty_level
        self.estimated_duration = estimated_duration
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'resource_type': self.resource_type,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'difficulty_level': self.difficulty_level,
            'estimated_duration': self.estimated_duration,
            'is_featured': self.is_featured,
            'is_active': self.is_active,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'views_count': self.views_count,
            'rating': self.rating
        }
    
    def __repr__(self):
        return f'<Resource {self.title} - {self.resource_type}>'