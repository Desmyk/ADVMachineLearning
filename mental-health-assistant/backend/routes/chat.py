from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.chat import ChatMessage, db
from models.user import User
from services.ai_chat import AIChat
from services.sentiment_analyzer import SentimentAnalyzer
import uuid
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Initialize services
ai_chat = AIChat()
sentiment_analyzer = SentimentAnalyzer()

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message and get AI response with sentiment analysis"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Analyze sentiment of user message
        sentiment_result = sentiment_analyzer.analyze_sentiment(user_message)
        
        # Get conversation history for context
        recent_messages = ChatMessage.query.filter_by(
            user_id=user_id, 
            session_id=session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(6).all()
        
        conversation_history = [msg.to_dict() for msg in reversed(recent_messages)]
        
        # Generate AI response
        ai_response = ai_chat.generate_response(
            user_message=user_message,
            sentiment_label=sentiment_result['label'],
            conversation_history=conversation_history
        )
        
        # Save user message
        user_chat_message = ChatMessage(
            user_id=user_id,
            message=user_message,
            is_user_message=True,
            sentiment_score=sentiment_result['compound'],
            sentiment_label=sentiment_result['label'],
            session_id=session_id
        )
        
        # Save AI response
        ai_chat_message = ChatMessage(
            user_id=user_id,
            message=ai_response,
            is_user_message=False,
            session_id=session_id
        )
        
        db.session.add(user_chat_message)
        db.session.add(ai_chat_message)
        db.session.commit()
        
        # Get response tone suggestions
        response_tone = sentiment_analyzer.get_supportive_response_tone(
            sentiment_result['label'], 
            sentiment_result['confidence']
        )
        
        logger.info(f"Chat message processed for user {user_id}, sentiment: {sentiment_result['label']}")
        
        return jsonify({
            'user_message': user_chat_message.to_dict(),
            'ai_response': ai_chat_message.to_dict(),
            'sentiment_analysis': sentiment_result,
            'response_tone': response_tone,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Send message error: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

@chat_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """Get user's chat sessions"""
    try:
        user_id = get_jwt_identity()
        
        # Get unique session IDs with latest message timestamp
        sessions_query = db.session.query(
            ChatMessage.session_id,
            db.func.max(ChatMessage.timestamp).label('last_message'),
            db.func.count(ChatMessage.id).label('message_count')
        ).filter_by(user_id=user_id).group_by(ChatMessage.session_id).all()
        
        sessions = []
        for session in sessions_query:
            # Get the first and last messages for preview
            first_message = ChatMessage.query.filter_by(
                user_id=user_id, 
                session_id=session.session_id,
                is_user_message=True
            ).order_by(ChatMessage.timestamp.asc()).first()
            
            last_message = ChatMessage.query.filter_by(
                user_id=user_id, 
                session_id=session.session_id
            ).order_by(ChatMessage.timestamp.desc()).first()
            
            session_data = {
                'session_id': session.session_id,
                'last_message_time': session.last_message.isoformat(),
                'message_count': session.message_count,
                'preview': first_message.message[:100] + '...' if first_message else '',
                'last_message_preview': last_message.message[:50] + '...' if last_message else ''
            }
            sessions.append(session_data)
        
        # Sort by most recent activity
        sessions.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        return jsonify({
            'sessions': sessions
        }), 200
        
    except Exception as e:
        logger.error(f"Get chat sessions error: {str(e)}")
        return jsonify({'error': 'Failed to get chat sessions'}), 500

@chat_bp.route('/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_session_messages(session_id):
    """Get messages from a specific chat session"""
    try:
        user_id = get_jwt_identity()
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        messages_query = ChatMessage.query.filter_by(
            user_id=user_id,
            session_id=session_id
        ).order_by(ChatMessage.timestamp.asc())
        
        messages = messages_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Get conversation summary
        all_messages = messages_query.all()
        conversation_summary = ai_chat.get_conversation_summary([msg.to_dict() for msg in all_messages])
        
        return jsonify({
            'session_id': session_id,
            'messages': [msg.to_dict() for msg in messages.items],
            'pagination': {
                'page': messages.page,
                'pages': messages.pages,
                'per_page': messages.per_page,
                'total': messages.total,
                'has_next': messages.has_next,
                'has_prev': messages.has_prev
            },
            'conversation_summary': conversation_summary
        }), 200
        
    except Exception as e:
        logger.error(f"Get session messages error: {str(e)}")
        return jsonify({'error': 'Failed to get session messages'}), 500

@chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    """Delete a chat session"""
    try:
        user_id = get_jwt_identity()
        
        # Delete all messages in the session
        deleted_count = ChatMessage.query.filter_by(
            user_id=user_id,
            session_id=session_id
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Deleted chat session {session_id} for user {user_id}, {deleted_count} messages removed")
        
        return jsonify({
            'message': 'Chat session deleted successfully',
            'deleted_messages': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete session error: {str(e)}")
        return jsonify({'error': 'Failed to delete session'}), 500

@chat_bp.route('/sentiment-trends', methods=['GET'])
@jwt_required()
def get_sentiment_trends():
    """Get sentiment trends from chat messages"""
    try:
        user_id = get_jwt_identity()
        
        # Get parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user messages with sentiment scores
        messages = ChatMessage.query.filter_by(
            user_id=user_id,
            is_user_message=True
        ).filter(
            ChatMessage.timestamp >= start_date,
            ChatMessage.sentiment_score.isnot(None)
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        if not messages:
            return jsonify({
                'sentiment_trends': [],
                'analysis': {
                    'trend': 'insufficient_data',
                    'average_sentiment': 0,
                    'total_messages': 0
                }
            }), 200
        
        # Prepare trend data
        sentiment_data = []
        for msg in messages:
            sentiment_data.append({
                'date': msg.timestamp.isoformat(),
                'sentiment_score': msg.sentiment_score,
                'sentiment_label': msg.sentiment_label,
                'message_preview': msg.message[:50] + '...'
            })
        
        # Analyze trends
        sentiment_scores = [msg.sentiment_score for msg in messages]
        trend_analysis = sentiment_analyzer.analyze_mood_trend(sentiment_scores)
        
        # Calculate additional statistics
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        positive_count = len([s for s in sentiment_scores if s > 0.1])
        negative_count = len([s for s in sentiment_scores if s < -0.1])
        neutral_count = len(sentiment_scores) - positive_count - negative_count
        
        return jsonify({
            'sentiment_trends': sentiment_data,
            'analysis': {
                **trend_analysis,
                'average_sentiment': average_sentiment,
                'total_messages': len(messages),
                'sentiment_distribution': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get sentiment trends error: {str(e)}")
        return jsonify({'error': 'Failed to get sentiment trends'}), 500

@chat_bp.route('/new-session', methods=['POST'])
@jwt_required()
def start_new_session():
    """Start a new chat session"""
    try:
        user_id = get_jwt_identity()
        
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Get user info for personalized greeting
        user = User.query.get(user_id)
        greeting = f"Hello {user.first_name}! I'm here to listen and support you. How are you feeling today?"
        
        # Create initial AI greeting message
        greeting_message = ChatMessage(
            user_id=user_id,
            message=greeting,
            is_user_message=False,
            session_id=session_id
        )
        
        db.session.add(greeting_message)
        db.session.commit()
        
        logger.info(f"New chat session started for user {user_id}: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'greeting_message': greeting_message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Start new session error: {str(e)}")
        return jsonify({'error': 'Failed to start new session'}), 500