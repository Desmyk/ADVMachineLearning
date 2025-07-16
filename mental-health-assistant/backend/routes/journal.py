from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.journal import JournalEntry, db
from services.journal_prompts import JournalPromptGenerator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
journal_bp = Blueprint('journal', __name__, url_prefix='/api/journal')

# Initialize prompt generator
prompt_generator = JournalPromptGenerator()

@journal_bp.route('/entries', methods=['POST'])
@jwt_required()
def create_entry():
    """Create a new journal entry"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('content'):
            return jsonify({'error': 'Content is required'}), 400
        
        # Create journal entry
        entry = JournalEntry(
            user_id=user_id,
            content=data['content'],
            title=data.get('title', '').strip(),
            prompt=data.get('prompt', ''),
            mood_before=data.get('mood_before'),
            mood_after=data.get('mood_after'),
            tags=data.get('tags', ''),
            is_private=data.get('is_private', True)
        )
        
        db.session.add(entry)
        db.session.commit()
        
        logger.info(f"Journal entry created for user {user_id}")
        
        return jsonify({
            'message': 'Journal entry created successfully',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create journal entry error: {str(e)}")
        return jsonify({'error': 'Failed to create journal entry'}), 500

@journal_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_entries():
    """Get user's journal entries"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        days = request.args.get('days', type=int)
        search = request.args.get('search', '').strip()
        
        # Base query
        query = JournalEntry.query.filter_by(user_id=user_id)
        
        # Date filtering
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(JournalEntry.date_created >= start_date)
        
        # Search filtering
        if search:
            query = query.filter(
                db.or_(
                    JournalEntry.title.contains(search),
                    JournalEntry.content.contains(search),
                    JournalEntry.tags.contains(search)
                )
            )
        
        # Order and paginate
        entries = query.order_by(JournalEntry.date_created.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries.items],
            'pagination': {
                'page': entries.page,
                'pages': entries.pages,
                'per_page': entries.per_page,
                'total': entries.total,
                'has_next': entries.has_next,
                'has_prev': entries.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get journal entries error: {str(e)}")
        return jsonify({'error': 'Failed to get journal entries'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_entry(entry_id):
    """Get a specific journal entry"""
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        return jsonify({
            'entry': entry.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get journal entry error: {str(e)}")
        return jsonify({'error': 'Failed to get journal entry'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_entry(entry_id):
    """Update a journal entry"""
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            entry.title = data['title'].strip()
        
        if 'content' in data:
            entry.content = data['content']
            entry.update_word_count()
        
        if 'mood_before' in data:
            entry.mood_before = data['mood_before']
        
        if 'mood_after' in data:
            entry.mood_after = data['mood_after']
        
        if 'tags' in data:
            entry.tags = data['tags']
        
        if 'is_private' in data:
            entry.is_private = data['is_private']
        
        entry.date_modified = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Journal entry {entry_id} updated for user {user_id}")
        
        return jsonify({
            'message': 'Journal entry updated successfully',
            'entry': entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update journal entry error: {str(e)}")
        return jsonify({'error': 'Failed to update journal entry'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_entry(entry_id):
    """Delete a journal entry"""
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        logger.info(f"Journal entry {entry_id} deleted for user {user_id}")
        
        return jsonify({
            'message': 'Journal entry deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete journal entry error: {str(e)}")
        return jsonify({'error': 'Failed to delete journal entry'}), 500

@journal_bp.route('/prompts/generate', methods=['POST'])
@jwt_required()
def generate_prompt():
    """Generate an AI-powered journal prompt"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get recent entries to avoid repetition
        recent_entries = JournalEntry.query.filter_by(user_id=user_id).order_by(
            JournalEntry.date_created.desc()
        ).limit(5).all()
        
        recent_entries_data = [{'prompt': entry.prompt} for entry in recent_entries if entry.prompt]
        
        # Generate prompt
        prompt_data = prompt_generator.generate_prompt(
            user_mood=data.get('mood'),
            recent_entries=recent_entries_data,
            user_preferences=data.get('preferences')
        )
        
        logger.info(f"Journal prompt generated for user {user_id}")
        
        return jsonify({
            'prompt_data': prompt_data
        }), 200
        
    except Exception as e:
        logger.error(f"Generate prompt error: {str(e)}")
        return jsonify({'error': 'Failed to generate prompt'}), 500

@journal_bp.route('/prompts/categories', methods=['GET'])
@jwt_required()
def get_prompt_categories():
    """Get available prompt categories"""
    try:
        categories = prompt_generator.get_available_categories()
        
        return jsonify({
            'categories': categories
        }), 200
        
    except Exception as e:
        logger.error(f"Get prompt categories error: {str(e)}")
        return jsonify({'error': 'Failed to get prompt categories'}), 500

@journal_bp.route('/prompts/category/<category>', methods=['GET'])
@jwt_required()
def get_prompt_by_category(category):
    """Get a prompt from a specific category"""
    try:
        prompt_data = prompt_generator.get_prompt_by_category(category)
        
        return jsonify({
            'prompt_data': prompt_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get prompt by category error: {str(e)}")
        return jsonify({'error': 'Failed to get prompt'}), 500

@journal_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get journal statistics and insights"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get entries in date range
        entries = JournalEntry.query.filter_by(user_id=user_id).filter(
            JournalEntry.date_created >= start_date
        ).all()
        
        if not entries:
            return jsonify({
                'statistics': {
                    'total_entries': 0,
                    'total_words': 0,
                    'average_words_per_entry': 0,
                    'mood_improvement': 0,
                    'most_active_day': None,
                    'common_tags': []
                }
            }), 200
        
        # Calculate statistics
        total_words = sum(entry.word_count for entry in entries)
        average_words = total_words / len(entries) if entries else 0
        
        # Mood improvement analysis
        mood_improvements = []
        for entry in entries:
            if entry.mood_before and entry.mood_after:
                improvement = entry.mood_after - entry.mood_before
                mood_improvements.append(improvement)
        
        average_mood_improvement = sum(mood_improvements) / len(mood_improvements) if mood_improvements else 0
        
        # Find most active day of week
        day_counts = {}
        for entry in entries:
            day_name = entry.date_created.strftime('%A')
            day_counts[day_name] = day_counts.get(day_name, 0) + 1
        
        most_active_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        
        # Common tags
        all_tags = []
        for entry in entries:
            if entry.tags:
                all_tags.extend([tag.strip() for tag in entry.tags.split(',') if tag.strip()])
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Writing streak
        writing_days = set()
        for entry in entries:
            writing_days.add(entry.date_created.date())
        
        current_streak = 0
        current_date = datetime.utcnow().date()
        while current_date in writing_days:
            current_streak += 1
            current_date -= timedelta(days=1)
        
        return jsonify({
            'statistics': {
                'total_entries': len(entries),
                'total_words': total_words,
                'average_words_per_entry': round(average_words, 1),
                'mood_improvement': round(average_mood_improvement, 2),
                'most_active_day': most_active_day,
                'common_tags': common_tags,
                'writing_streak': current_streak,
                'unique_writing_days': len(writing_days),
                'date_range': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat()
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get journal statistics error: {str(e)}")
        return jsonify({'error': 'Failed to get journal statistics'}), 500

@journal_bp.route('/weekly-prompts', methods=['GET'])
@jwt_required()
def get_weekly_prompts():
    """Get a set of prompts for the week"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's recent mood average for context
        recent_moods = db.session.query(db.func.avg(db.text('score'))).select_from(
            db.text('moods')
        ).filter(
            db.text('user_id = :user_id')
        ).params(user_id=user_id).scalar()
        
        weekly_prompts = prompt_generator.get_weekly_prompts(recent_moods)
        
        logger.info(f"Weekly prompts generated for user {user_id}")
        
        return jsonify({
            'weekly_prompts': weekly_prompts
        }), 200
        
    except Exception as e:
        logger.error(f"Get weekly prompts error: {str(e)}")
        return jsonify({'error': 'Failed to get weekly prompts'}), 500