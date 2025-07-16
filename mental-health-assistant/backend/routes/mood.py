from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.mood import Mood, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
mood_bp = Blueprint('mood', __name__, url_prefix='/api/mood')

@mood_bp.route('/log', methods=['POST'])
@jwt_required()
def log_mood():
    """Log a new mood entry"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('score') or not isinstance(data.get('score'), int):
            return jsonify({'error': 'Mood score (1-5) is required'}), 400
        
        score = data['score']
        if score < 1 or score > 5:
            return jsonify({'error': 'Mood score must be between 1 and 5'}), 400
        
        # Create mood entry
        mood = Mood(
            user_id=user_id,
            score=score,
            notes=data.get('notes', '').strip(),
            tags=data.get('tags', '')
        )
        
        db.session.add(mood)
        db.session.commit()
        
        logger.info(f"Mood logged for user {user_id}: {score}/5")
        
        return jsonify({
            'message': 'Mood logged successfully',
            'mood': mood.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Log mood error: {str(e)}")
        return jsonify({'error': 'Failed to log mood'}), 500

@mood_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_mood_entries():
    """Get user's mood entries with optional filtering"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        days = request.args.get('days', 30, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query moods
        moods_query = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= start_date
        ).order_by(Mood.date_recorded.desc())
        
        moods = moods_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'moods': [mood.to_dict() for mood in moods.items],
            'pagination': {
                'page': moods.page,
                'pages': moods.pages,
                'per_page': moods.per_page,
                'total': moods.total,
                'has_next': moods.has_next,
                'has_prev': moods.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get mood entries error: {str(e)}")
        return jsonify({'error': 'Failed to get mood entries'}), 500

@mood_bp.route('/entries/<int:mood_id>', methods=['PUT'])
@jwt_required()
def update_mood_entry(mood_id):
    """Update a mood entry"""
    try:
        user_id = get_jwt_identity()
        mood = Mood.query.filter_by(id=mood_id, user_id=user_id).first()
        
        if not mood:
            return jsonify({'error': 'Mood entry not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'score' in data:
            score = data['score']
            if not isinstance(score, int) or score < 1 or score > 5:
                return jsonify({'error': 'Mood score must be between 1 and 5'}), 400
            mood.score = score
        
        if 'notes' in data:
            mood.notes = data['notes'].strip()
        
        if 'tags' in data:
            mood.tags = data['tags']
        
        db.session.commit()
        
        logger.info(f"Mood entry {mood_id} updated for user {user_id}")
        
        return jsonify({
            'message': 'Mood entry updated successfully',
            'mood': mood.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update mood entry error: {str(e)}")
        return jsonify({'error': 'Failed to update mood entry'}), 500

@mood_bp.route('/entries/<int:mood_id>', methods=['DELETE'])
@jwt_required()
def delete_mood_entry(mood_id):
    """Delete a mood entry"""
    try:
        user_id = get_jwt_identity()
        mood = Mood.query.filter_by(id=mood_id, user_id=user_id).first()
        
        if not mood:
            return jsonify({'error': 'Mood entry not found'}), 404
        
        db.session.delete(mood)
        db.session.commit()
        
        logger.info(f"Mood entry {mood_id} deleted for user {user_id}")
        
        return jsonify({
            'message': 'Mood entry deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete mood entry error: {str(e)}")
        return jsonify({'error': 'Failed to delete mood entry'}), 500

@mood_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_mood_trends():
    """Get mood trends and analytics"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get mood entries
        moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= start_date
        ).order_by(Mood.date_recorded.asc()).all()
        
        if not moods:
            return jsonify({
                'trends': [],
                'statistics': {
                    'total_entries': 0,
                    'average_mood': 0,
                    'trend_direction': 'insufficient_data'
                }
            }), 200
        
        # Prepare trend data (daily averages)
        daily_moods = {}
        for mood in moods:
            date_key = mood.date_recorded.date().isoformat()
            if date_key not in daily_moods:
                daily_moods[date_key] = []
            daily_moods[date_key].append(mood.score)
        
        # Calculate daily averages
        trend_data = []
        for date_str, scores in sorted(daily_moods.items()):
            avg_score = sum(scores) / len(scores)
            trend_data.append({
                'date': date_str,
                'average_mood': round(avg_score, 2),
                'entries_count': len(scores),
                'mood_range': {
                    'min': min(scores),
                    'max': max(scores)
                }
            })
        
        # Calculate statistics
        all_scores = [mood.score for mood in moods]
        average_mood = sum(all_scores) / len(all_scores)
        
        # Trend analysis
        if len(trend_data) >= 7:
            recent_week = trend_data[-7:]
            previous_week = trend_data[-14:-7] if len(trend_data) >= 14 else trend_data[:-7]
            
            recent_avg = sum(day['average_mood'] for day in recent_week) / len(recent_week)
            previous_avg = sum(day['average_mood'] for day in previous_week) / len(previous_week) if previous_week else recent_avg
            
            if recent_avg > previous_avg + 0.2:
                trend_direction = 'improving'
            elif recent_avg < previous_avg - 0.2:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        # Mood distribution
        mood_distribution = {str(i): all_scores.count(i) for i in range(1, 6)}
        
        # Most common tags
        all_tags = []
        for mood in moods:
            if mood.tags:
                all_tags.extend([tag.strip() for tag in mood.tags.split(',') if tag.strip()])
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'trends': trend_data,
            'statistics': {
                'total_entries': len(moods),
                'average_mood': round(average_mood, 2),
                'trend_direction': trend_direction,
                'mood_distribution': mood_distribution,
                'date_range': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat()
                },
                'common_tags': common_tags
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get mood trends error: {str(e)}")
        return jsonify({'error': 'Failed to get mood trends'}), 500

@mood_bp.route('/weekly-summary', methods=['GET'])
@jwt_required()
def get_weekly_summary():
    """Get weekly mood summary"""
    try:
        user_id = get_jwt_identity()
        
        # Calculate date range for the current week
        today = datetime.utcnow().date()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Get moods for the current week
        moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= datetime.combine(week_start, datetime.min.time()),
            Mood.date_recorded <= datetime.combine(week_end, datetime.max.time())
        ).order_by(Mood.date_recorded.asc()).all()
        
        # Organize by day of week
        week_data = {}
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_name = day_date.strftime('%A')
            week_data[day_name] = {
                'date': day_date.isoformat(),
                'moods': [],
                'average': 0,
                'entries_count': 0
            }
        
        # Fill in actual mood data
        for mood in moods:
            day_name = mood.date_recorded.strftime('%A')
            if day_name in week_data:
                week_data[day_name]['moods'].append(mood.to_dict())
        
        # Calculate averages
        for day_data in week_data.values():
            if day_data['moods']:
                scores = [mood['score'] for mood in day_data['moods']]
                day_data['average'] = sum(scores) / len(scores)
                day_data['entries_count'] = len(scores)
        
        # Overall week statistics
        week_moods = [mood.score for mood in moods]
        week_average = sum(week_moods) / len(week_moods) if week_moods else 0
        
        return jsonify({
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'daily_data': week_data,
            'week_summary': {
                'total_entries': len(moods),
                'average_mood': round(week_average, 2),
                'best_day': max(week_data.items(), key=lambda x: x[1]['average'])[0] if any(d['entries_count'] > 0 for d in week_data.values()) else None,
                'most_active_day': max(week_data.items(), key=lambda x: x[1]['entries_count'])[0] if moods else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get weekly summary error: {str(e)}")
        return jsonify({'error': 'Failed to get weekly summary'}), 500

@mood_bp.route('/check-today', methods=['GET'])
@jwt_required()
def check_today_mood():
    """Check if user has logged mood today"""
    try:
        user_id = get_jwt_identity()
        
        # Get today's date range
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Check for today's mood entries
        today_moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= today_start,
            Mood.date_recorded <= today_end
        ).all()
        
        return jsonify({
            'has_logged_today': len(today_moods) > 0,
            'entries_count': len(today_moods),
            'entries': [mood.to_dict() for mood in today_moods]
        }), 200
        
    except Exception as e:
        logger.error(f"Check today mood error: {str(e)}")
        return jsonify({'error': 'Failed to check today\'s mood'}), 500