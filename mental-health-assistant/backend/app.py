from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import logging
import os

# Import models and database
from models.user import db, bcrypt
from models import User, Mood, ChatMessage, JournalEntry, Resource

# Import routes
from routes import auth_bp, chat_bp, mood_bp, journal_bp, resources_bp, dashboard_bp

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(dashboard_bp)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401
    
    # Health check endpoint
    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Mental Health AI Assistant API',
            'version': '1.0.0'
        })
    
    @app.route('/api/health')
    def api_health():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'ai_services': 'available'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Seed initial data if needed
        seed_initial_data()
    
    return app

def seed_initial_data():
    """Seed the database with initial resources and data"""
    try:
        # Check if resources already exist
        if Resource.query.count() > 0:
            return
        
        # Create sample mental health resources
        sample_resources = [
            {
                'title': 'Guided Meditation for Anxiety',
                'description': 'A 10-minute guided meditation to help calm anxiety and racing thoughts.',
                'url': 'https://example.com/anxiety-meditation',
                'resource_type': 'video',
                'category': 'anxiety',
                'tags': 'meditation,anxiety,relaxation',
                'difficulty_level': 'beginner',
                'estimated_duration': 10,
                'is_featured': True,
                'rating': 4.8
            },
            {
                'title': 'Understanding Depression: A Comprehensive Guide',
                'description': 'An in-depth article about depression symptoms, causes, and treatment options.',
                'url': 'https://example.com/depression-guide',
                'resource_type': 'article',
                'category': 'depression',
                'tags': 'depression,mental health,treatment',
                'difficulty_level': 'intermediate',
                'estimated_duration': 15,
                'is_featured': True,
                'rating': 4.7
            },
            {
                'title': 'Breathing Exercises for Stress Relief',
                'description': 'Simple breathing techniques you can use anywhere to manage stress.',
                'url': 'https://example.com/breathing-exercises',
                'resource_type': 'guide',
                'category': 'stress_management',
                'tags': 'breathing,stress,techniques',
                'difficulty_level': 'beginner',
                'estimated_duration': 5,
                'is_featured': False,
                'rating': 4.6
            },
            {
                'title': 'Mindfulness in Daily Life',
                'description': 'Learn how to incorporate mindfulness practices into your everyday routine.',
                'url': 'https://example.com/mindfulness-daily',
                'resource_type': 'article',
                'category': 'mindfulness',
                'tags': 'mindfulness,daily practice,awareness',
                'difficulty_level': 'beginner',
                'estimated_duration': 12,
                'is_featured': True,
                'rating': 4.9
            },
            {
                'title': 'Cognitive Behavioral Therapy Basics',
                'description': 'Introduction to CBT techniques for managing negative thought patterns.',
                'url': 'https://example.com/cbt-basics',
                'resource_type': 'article',
                'category': 'therapy',
                'tags': 'CBT,therapy,thoughts',
                'difficulty_level': 'intermediate',
                'estimated_duration': 20,
                'is_featured': False,
                'rating': 4.5
            },
            {
                'title': 'Sleep Hygiene for Better Mental Health',
                'description': 'How good sleep habits can improve your overall mental wellbeing.',
                'url': 'https://example.com/sleep-hygiene',
                'resource_type': 'guide',
                'category': 'general_wellbeing',
                'tags': 'sleep,hygiene,mental health',
                'difficulty_level': 'beginner',
                'estimated_duration': 8,
                'is_featured': False,
                'rating': 4.4
            },
            {
                'title': 'Crisis Support Resources',
                'description': 'Important phone numbers and resources for mental health crises.',
                'url': 'https://example.com/crisis-support',
                'resource_type': 'tool',
                'category': 'crisis_support',
                'tags': 'crisis,emergency,support',
                'difficulty_level': 'beginner',
                'estimated_duration': 2,
                'is_featured': True,
                'rating': 5.0
            },
            {
                'title': 'Building Resilience: A Personal Journey',
                'description': 'A video series about developing emotional resilience and coping skills.',
                'url': 'https://example.com/resilience-journey',
                'resource_type': 'video',
                'category': 'growth',
                'tags': 'resilience,coping,personal growth',
                'difficulty_level': 'intermediate',
                'estimated_duration': 25,
                'is_featured': False,
                'rating': 4.6
            }
        ]
        
        for resource_data in sample_resources:
            resource = Resource(**resource_data)
            db.session.add(resource)
        
        db.session.commit()
        print("Initial resources seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding initial data: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    app = create_app()
    
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Mental Health AI Assistant API on port {port}")
    print(f"Debug mode: {debug}")
    print("Available endpoints:")
    print("  - GET  /                    - Health check")
    print("  - GET  /api/health          - API health check")
    print("  - POST /api/auth/register   - User registration")
    print("  - POST /api/auth/login      - User login")
    print("  - GET  /api/dashboard/overview - Dashboard overview")
    print("  - POST /api/chat/send       - Send chat message")
    print("  - POST /api/mood/log        - Log mood")
    print("  - POST /api/journal/entries - Create journal entry")
    print("  - GET  /api/resources/      - Get resources")
    print("")
    
    app.run(host='0.0.0.0', port=port, debug=debug)