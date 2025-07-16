from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.resource import Resource, db
import logging

logger = logging.getLogger(__name__)
resources_bp = Blueprint('resources', __name__, url_prefix='/api/resources')

@resources_bp.route('/', methods=['GET'])
@jwt_required()
def get_resources():
    """Get curated mental health resources"""
    try:
        # Query parameters
        resource_type = request.args.get('type')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        featured_only = request.args.get('featured', '').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        # Base query - only active resources
        query = Resource.query.filter_by(is_active=True)
        
        # Apply filters
        if resource_type:
            query = query.filter_by(resource_type=resource_type)
        
        if category:
            query = query.filter_by(category=category)
        
        if difficulty:
            query = query.filter_by(difficulty_level=difficulty)
        
        if featured_only:
            query = query.filter_by(is_featured=True)
        
        if search:
            query = query.filter(
                db.or_(
                    Resource.title.contains(search),
                    Resource.description.contains(search),
                    Resource.tags.contains(search)
                )
            )
        
        # Order by featured first, then by rating/views
        query = query.order_by(
            Resource.is_featured.desc(),
            Resource.rating.desc(),
            Resource.views_count.desc()
        )
        
        # Paginate
        resources = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'resources': [resource.to_dict() for resource in resources.items],
            'pagination': {
                'page': resources.page,
                'pages': resources.pages,
                'per_page': resources.per_page,
                'total': resources.total,
                'has_next': resources.has_next,
                'has_prev': resources.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get resources error: {str(e)}")
        return jsonify({'error': 'Failed to get resources'}), 500

@resources_bp.route('/<int:resource_id>', methods=['GET'])
@jwt_required()
def get_resource(resource_id):
    """Get a specific resource and increment view count"""
    try:
        resource = Resource.query.filter_by(id=resource_id, is_active=True).first()
        
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Increment view count
        resource.increment_views()
        db.session.commit()
        
        return jsonify({
            'resource': resource.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get resource error: {str(e)}")
        return jsonify({'error': 'Failed to get resource'}), 500

@resources_bp.route('/featured', methods=['GET'])
@jwt_required()
def get_featured_resources():
    """Get featured resources"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        resources = Resource.query.filter_by(
            is_featured=True,
            is_active=True
        ).order_by(
            Resource.rating.desc(),
            Resource.views_count.desc()
        ).limit(limit).all()
        
        return jsonify({
            'featured_resources': [resource.to_dict() for resource in resources]
        }), 200
        
    except Exception as e:
        logger.error(f"Get featured resources error: {str(e)}")
        return jsonify({'error': 'Failed to get featured resources'}), 500

@resources_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get available resource categories"""
    try:
        # Get distinct categories with counts
        categories_query = db.session.query(
            Resource.category,
            db.func.count(Resource.id).label('count')
        ).filter_by(is_active=True).group_by(Resource.category).all()
        
        categories = [
            {
                'category': cat.category,
                'count': cat.count,
                'display_name': cat.category.replace('_', ' ').title() if cat.category else 'General'
            }
            for cat in categories_query if cat.category
        ]
        
        # Get distinct resource types
        types_query = db.session.query(
            Resource.resource_type,
            db.func.count(Resource.id).label('count')
        ).filter_by(is_active=True).group_by(Resource.resource_type).all()
        
        resource_types = [
            {
                'type': rt.resource_type,
                'count': rt.count,
                'display_name': rt.resource_type.replace('_', ' ').title()
            }
            for rt in types_query
        ]
        
        return jsonify({
            'categories': categories,
            'resource_types': resource_types,
            'difficulty_levels': [
                {'level': 'beginner', 'display_name': 'Beginner'},
                {'level': 'intermediate', 'display_name': 'Intermediate'},
                {'level': 'advanced', 'display_name': 'Advanced'}
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        return jsonify({'error': 'Failed to get categories'}), 500

@resources_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get personalized resource recommendations based on user activity"""
    try:
        user_id = get_jwt_identity()
        
        # For now, return popular resources in relevant categories
        # In a more advanced implementation, this would use user's mood trends,
        # chat sentiment, and journal analysis to recommend specific resources
        
        # Get user's recent mood and sentiment data to inform recommendations
        from models.mood import Mood
        from models.chat import ChatMessage
        from datetime import datetime, timedelta
        
        # Recent mood analysis
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= recent_date
        ).all()
        
        recent_chats = ChatMessage.query.filter_by(user_id=user_id, is_user_message=True).filter(
            ChatMessage.timestamp >= recent_date
        ).all()
        
        # Determine recommendation categories based on user state
        recommended_categories = []
        
        if recent_moods:
            avg_mood = sum(mood.score for mood in recent_moods) / len(recent_moods)
            if avg_mood < 3:
                recommended_categories.extend(['coping_strategies', 'depression', 'anxiety'])
            elif avg_mood > 4:
                recommended_categories.extend(['mindfulness', 'growth', 'happiness'])
            else:
                recommended_categories.extend(['general_wellbeing', 'stress_management'])
        
        if recent_chats:
            negative_sentiments = [chat for chat in recent_chats if chat.sentiment_score and chat.sentiment_score < -0.1]
            if len(negative_sentiments) > len(recent_chats) * 0.6:  # More than 60% negative
                recommended_categories.extend(['support', 'crisis_help', 'therapy'])
        
        # Default categories if no user data
        if not recommended_categories:
            recommended_categories = ['general_wellbeing', 'mindfulness', 'stress_management']
        
        # Get resources from recommended categories
        resources = Resource.query.filter(
            Resource.category.in_(recommended_categories),
            Resource.is_active == True
        ).order_by(
            Resource.is_featured.desc(),
            Resource.rating.desc()
        ).limit(15).all()
        
        # If not enough resources, add some general popular ones
        if len(resources) < 10:
            additional_resources = Resource.query.filter_by(
                is_active=True
            ).order_by(
                Resource.views_count.desc(),
                Resource.rating.desc()
            ).limit(10 - len(resources)).all()
            resources.extend(additional_resources)
        
        return jsonify({
            'recommendations': [resource.to_dict() for resource in resources],
            'recommendation_reason': 'Based on your recent activity and mood patterns',
            'categories_focused': list(set(recommended_categories))
        }), 200
        
    except Exception as e:
        logger.error(f"Get recommendations error: {str(e)}")
        return jsonify({'error': 'Failed to get recommendations'}), 500

@resources_bp.route('/search', methods=['GET'])
@jwt_required()
def search_resources():
    """Advanced search for resources"""
    try:
        query_text = request.args.get('q', '').strip()
        resource_type = request.args.get('type')
        category = request.args.get('category')
        min_rating = request.args.get('min_rating', type=float)
        max_duration = request.args.get('max_duration', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Build search query
        query = Resource.query.filter_by(is_active=True)
        
        # Text search
        query = query.filter(
            db.or_(
                Resource.title.contains(query_text),
                Resource.description.contains(query_text),
                Resource.tags.contains(query_text)
            )
        )
        
        # Apply filters
        if resource_type:
            query = query.filter_by(resource_type=resource_type)
        
        if category:
            query = query.filter_by(category=category)
        
        if min_rating:
            query = query.filter(Resource.rating >= min_rating)
        
        if max_duration:
            query = query.filter(
                db.or_(
                    Resource.estimated_duration <= max_duration,
                    Resource.estimated_duration.is_(None)
                )
            )
        
        # Order by relevance (this is simplified - could be improved with full-text search)
        query = query.order_by(
            Resource.rating.desc(),
            Resource.views_count.desc()
        )
        
        # Paginate
        results = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'search_results': [resource.to_dict() for resource in results.items],
            'search_query': query_text,
            'pagination': {
                'page': results.page,
                'pages': results.pages,
                'per_page': results.per_page,
                'total': results.total,
                'has_next': results.has_next,
                'has_prev': results.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Search resources error: {str(e)}")
        return jsonify({'error': 'Failed to search resources'}), 500

# Admin endpoints (would typically require admin authentication)
@resources_bp.route('/admin/create', methods=['POST'])
@jwt_required()
def create_resource():
    """Create a new resource (admin function)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'url', 'resource_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create resource
        resource = Resource(
            title=data['title'],
            url=data['url'],
            resource_type=data['resource_type'],
            description=data.get('description', ''),
            category=data.get('category'),
            tags=data.get('tags', ''),
            difficulty_level=data.get('difficulty_level', 'beginner'),
            estimated_duration=data.get('estimated_duration')
        )
        
        if data.get('is_featured'):
            resource.is_featured = True
        
        db.session.add(resource)
        db.session.commit()
        
        logger.info(f"Resource created: {resource.title}")
        
        return jsonify({
            'message': 'Resource created successfully',
            'resource': resource.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create resource error: {str(e)}")
        return jsonify({'error': 'Failed to create resource'}), 500