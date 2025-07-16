from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.mood import Mood
from models.chat import ChatMessage
from models.journal import JournalEntry
from models.resource import Resource, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """Get comprehensive dashboard overview"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user data
        user = User.query.get(user_id)
        
        # Recent moods
        recent_moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= start_date
        ).order_by(Mood.date_recorded.desc()).all()
        
        # Recent journal entries
        recent_journals = JournalEntry.query.filter_by(user_id=user_id).filter(
            JournalEntry.date_created >= start_date
        ).order_by(JournalEntry.date_created.desc()).all()
        
        # Recent chat activity
        recent_chats = ChatMessage.query.filter_by(user_id=user_id, is_user_message=True).filter(
            ChatMessage.timestamp >= start_date
        ).order_by(ChatMessage.timestamp.desc()).all()
        
        # Calculate summary statistics
        mood_scores = [mood.score for mood in recent_moods]
        avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
        
        chat_sentiments = [chat.sentiment_score for chat in recent_chats if chat.sentiment_score is not None]
        avg_sentiment = sum(chat_sentiments) / len(chat_sentiments) if chat_sentiments else 0
        
        # Mood trend analysis
        mood_trend = 'stable'
        if len(mood_scores) >= 7:
            recent_week = mood_scores[:7]
            earlier_week = mood_scores[7:14] if len(mood_scores) >= 14 else mood_scores[7:]
            
            if earlier_week:
                recent_avg = sum(recent_week) / len(recent_week)
                earlier_avg = sum(earlier_week) / len(earlier_week)
                
                if recent_avg > earlier_avg + 0.3:
                    mood_trend = 'improving'
                elif recent_avg < earlier_avg - 0.3:
                    mood_trend = 'declining'
        
        # Activity summary
        activity_summary = {
            'moods_logged': len(recent_moods),
            'journal_entries': len(recent_journals),
            'chat_messages': len(recent_chats),
            'total_words_written': sum(entry.word_count for entry in recent_journals)
        }
        
        # Recent activity timeline
        timeline = []
        
        # Add mood entries to timeline
        for mood in recent_moods[:5]:
            timeline.append({
                'type': 'mood',
                'date': mood.date_recorded.isoformat(),
                'data': mood.to_dict(),
                'description': f"Logged mood: {mood.mood_label}"
            })
        
        # Add journal entries to timeline
        for journal in recent_journals[:5]:
            timeline.append({
                'type': 'journal',
                'date': journal.date_created.isoformat(),
                'data': {'title': journal.title, 'word_count': journal.word_count},
                'description': f"Wrote journal entry: {journal.title or 'Untitled'}"
            })
        
        # Add chat sessions to timeline
        chat_sessions = {}
        for chat in recent_chats:
            session_id = chat.session_id
            if session_id not in chat_sessions:
                chat_sessions[session_id] = {
                    'date': chat.timestamp,
                    'message_count': 0,
                    'avg_sentiment': 0,
                    'sentiments': []
                }
            chat_sessions[session_id]['message_count'] += 1
            if chat.sentiment_score is not None:
                chat_sessions[session_id]['sentiments'].append(chat.sentiment_score)
        
        for session_id, session_data in list(chat_sessions.items())[:3]:
            avg_session_sentiment = (sum(session_data['sentiments']) / 
                                   len(session_data['sentiments'])) if session_data['sentiments'] else 0
            timeline.append({
                'type': 'chat',
                'date': session_data['date'].isoformat(),
                'data': {
                    'message_count': session_data['message_count'],
                    'avg_sentiment': avg_session_sentiment
                },
                'description': f"Chat session with {session_data['message_count']} messages"
            })
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'], reverse=True)
        
        # Today's summary
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= today_start,
            Mood.date_recorded <= today_end
        ).all()
        
        today_journals = JournalEntry.query.filter_by(user_id=user_id).filter(
            JournalEntry.date_created >= today_start,
            JournalEntry.date_created <= today_end
        ).all()
        
        today_chats = ChatMessage.query.filter_by(user_id=user_id, is_user_message=True).filter(
            ChatMessage.timestamp >= today_start,
            ChatMessage.timestamp <= today_end
        ).all()
        
        overview = {
            'user_info': {
                'name': f"{user.first_name} {user.last_name}",
                'member_since': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            },
            'period_summary': {
                'date_range': {
                    'start': start_date.date().isoformat(),
                    'end': end_date.date().isoformat(),
                    'days': days
                },
                'mood_summary': {
                    'average_mood': round(avg_mood, 2),
                    'total_entries': len(recent_moods),
                    'trend': mood_trend
                },
                'sentiment_summary': {
                    'average_sentiment': round(avg_sentiment, 3),
                    'total_messages': len(recent_chats)
                },
                'journal_summary': {
                    'total_entries': len(recent_journals),
                    'total_words': sum(entry.word_count for entry in recent_journals)
                }
            },
            'today_summary': {
                'moods_logged': len(today_moods),
                'journal_entries': len(today_journals),
                'chat_messages': len(today_chats),
                'has_activity': len(today_moods) > 0 or len(today_journals) > 0 or len(today_chats) > 0
            },
            'activity_summary': activity_summary,
            'recent_timeline': timeline[:10]
        }
        
        return jsonify({
            'overview': overview
        }), 200
        
    except Exception as e:
        logger.error(f"Get dashboard overview error: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard overview'}), 500

@dashboard_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    """Get AI-powered insights and recommendations"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user data for analysis
        moods = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= start_date
        ).order_by(Mood.date_recorded.asc()).all()
        
        chats = ChatMessage.query.filter_by(user_id=user_id, is_user_message=True).filter(
            ChatMessage.timestamp >= start_date,
            ChatMessage.sentiment_score.isnot(None)
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        journals = JournalEntry.query.filter_by(user_id=user_id).filter(
            JournalEntry.date_created >= start_date
        ).order_by(JournalEntry.date_created.asc()).all()
        
        insights = []
        
        # Mood pattern insights
        if moods:
            mood_scores = [mood.score for mood in moods]
            avg_mood = sum(mood_scores) / len(mood_scores)
            
            # Weekly patterns
            weekly_moods = {}
            for mood in moods:
                week_day = mood.date_recorded.strftime('%A')
                if week_day not in weekly_moods:
                    weekly_moods[week_day] = []
                weekly_moods[week_day].append(mood.score)
            
            # Find best and worst days
            day_averages = {day: sum(scores)/len(scores) for day, scores in weekly_moods.items()}
            if day_averages:
                best_day = max(day_averages.items(), key=lambda x: x[1])
                worst_day = min(day_averages.items(), key=lambda x: x[1])
                
                insights.append({
                    'type': 'mood_pattern',
                    'title': 'Weekly Mood Patterns',
                    'description': f"Your mood tends to be highest on {best_day[0]}s (avg: {best_day[1]:.1f}) and lowest on {worst_day[0]}s (avg: {worst_day[1]:.1f})",
                    'data': day_averages,
                    'actionable': True,
                    'suggestion': f"Consider planning self-care activities for {worst_day[0]}s to help improve your mood on that day."
                })
            
            # Mood trend insight
            if len(mood_scores) >= 14:
                recent_half = mood_scores[-len(mood_scores)//2:]
                earlier_half = mood_scores[:len(mood_scores)//2]
                
                recent_avg = sum(recent_half) / len(recent_half)
                earlier_avg = sum(earlier_half) / len(earlier_half)
                
                if recent_avg > earlier_avg + 0.2:
                    insights.append({
                        'type': 'mood_trend',
                        'title': 'Positive Mood Trend',
                        'description': f"Your mood has been improving over the past {days} days. Recent average: {recent_avg:.1f}, Earlier average: {earlier_avg:.1f}",
                        'data': {'recent_avg': recent_avg, 'earlier_avg': earlier_avg},
                        'actionable': True,
                        'suggestion': "Keep up whatever you've been doing! Consider reflecting on what changes have contributed to this improvement."
                    })
                elif recent_avg < earlier_avg - 0.2:
                    insights.append({
                        'type': 'mood_trend',
                        'title': 'Declining Mood Pattern',
                        'description': f"Your mood has been declining recently. Recent average: {recent_avg:.1f}, Earlier average: {earlier_avg:.1f}",
                        'data': {'recent_avg': recent_avg, 'earlier_avg': earlier_avg},
                        'actionable': True,
                        'suggestion': "Consider reaching out for support, practicing self-care, or reviewing recent stressors that might be affecting your mood."
                    })
        
        # Sentiment and chat insights
        if chats:
            sentiment_scores = [chat.sentiment_score for chat in chats]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            positive_ratio = len([s for s in sentiment_scores if s > 0.1]) / len(sentiment_scores)
            negative_ratio = len([s for s in sentiment_scores if s < -0.1]) / len(sentiment_scores)
            
            if positive_ratio > 0.6:
                insights.append({
                    'type': 'communication_pattern',
                    'title': 'Positive Communication',
                    'description': f"{positive_ratio*100:.0f}% of your messages have been positive in tone",
                    'data': {'positive_ratio': positive_ratio, 'avg_sentiment': avg_sentiment},
                    'actionable': False,
                    'suggestion': "Your positive communication style is a strength!"
                })
            elif negative_ratio > 0.6:
                insights.append({
                    'type': 'communication_pattern',
                    'title': 'Communication Concerns',
                    'description': f"{negative_ratio*100:.0f}% of your messages have been negative in tone",
                    'data': {'negative_ratio': negative_ratio, 'avg_sentiment': avg_sentiment},
                    'actionable': True,
                    'suggestion': "Consider focusing on self-compassion and positive self-talk. The resources section has helpful guides on this."
                })
        
        # Journal insights
        if journals:
            total_words = sum(entry.word_count for entry in journals)
            avg_words = total_words / len(journals)
            
            # Mood improvement through journaling
            mood_improvements = []
            for entry in journals:
                if entry.mood_before and entry.mood_after:
                    improvement = entry.mood_after - entry.mood_before
                    mood_improvements.append(improvement)
            
            if mood_improvements:
                avg_improvement = sum(mood_improvements) / len(mood_improvements)
                if avg_improvement > 0.3:
                    insights.append({
                        'type': 'journaling_benefit',
                        'title': 'Journaling Helps Your Mood',
                        'description': f"Journaling consistently improves your mood by an average of {avg_improvement:.1f} points",
                        'data': {'avg_improvement': avg_improvement, 'entries_tracked': len(mood_improvements)},
                        'actionable': True,
                        'suggestion': "Continue your journaling practice! It's clearly having a positive impact on your wellbeing."
                    })
            
            # Writing consistency
            writing_days = set(entry.date_created.date() for entry in journals)
            consistency_rate = len(writing_days) / days
            
            if consistency_rate > 0.5:
                insights.append({
                    'type': 'consistency',
                    'title': 'Strong Writing Habit',
                    'description': f"You've written in your journal {len(writing_days)} out of {days} days ({consistency_rate*100:.0f}%)",
                    'data': {'writing_days': len(writing_days), 'total_days': days},
                    'actionable': False,
                    'suggestion': "Excellent consistency with your journaling practice!"
                })
        
        # Generate recommendations based on insights
        recommendations = []
        
        if len(insights) == 0:
            recommendations.append({
                'type': 'engagement',
                'title': 'Start Building Habits',
                'description': 'Regular mood tracking and journaling can provide valuable insights into your mental health patterns.',
                'priority': 'high'
            })
        
        # Mood-based recommendations
        if moods:
            recent_moods = [mood.score for mood in moods[-7:]]  # Last week
            if recent_moods and sum(recent_moods) / len(recent_moods) < 3:
                recommendations.append({
                    'type': 'support',
                    'title': 'Consider Additional Support',
                    'description': 'Your recent mood scores suggest you might benefit from additional coping strategies or professional support.',
                    'priority': 'high'
                })
        
        return jsonify({
            'insights': insights,
            'recommendations': recommendations,
            'analysis_period': {
                'start': start_date.date().isoformat(),
                'end': end_date.date().isoformat(),
                'days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get insights error: {str(e)}")
        return jsonify({'error': 'Failed to get insights'}), 500

@dashboard_bp.route('/goals', methods=['GET'])
@jwt_required()
def get_goals():
    """Get suggested goals and progress tracking"""
    try:
        user_id = get_jwt_identity()
        
        # Calculate some basic goals based on user activity
        goals = [
            {
                'id': 'mood_tracking',
                'title': 'Daily Mood Tracking',
                'description': 'Log your mood every day for better self-awareness',
                'target': 7,  # 7 days
                'current': 0,  # Will be calculated
                'type': 'daily_habit',
                'category': 'mood'
            },
            {
                'id': 'journal_writing',
                'title': 'Weekly Journaling',
                'description': 'Write at least 3 journal entries per week',
                'target': 3,
                'current': 0,
                'type': 'weekly_habit',
                'category': 'journaling'
            },
            {
                'id': 'ai_conversation',
                'title': 'Regular Check-ins',
                'description': 'Have meaningful conversations with the AI assistant',
                'target': 2,  # 2 sessions per week
                'current': 0,
                'type': 'weekly_habit',
                'category': 'communication'
            }
        ]
        
        # Calculate current progress
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Daily mood tracking (last 7 days)
        mood_days = Mood.query.filter_by(user_id=user_id).filter(
            Mood.date_recorded >= datetime.combine(today - timedelta(days=7), datetime.min.time())
        ).all()
        
        unique_mood_days = len(set(mood.date_recorded.date() for mood in mood_days))
        goals[0]['current'] = unique_mood_days
        goals[0]['progress'] = min(100, (unique_mood_days / 7) * 100)
        
        # Weekly journaling (current week)
        week_journals = JournalEntry.query.filter_by(user_id=user_id).filter(
            JournalEntry.date_created >= datetime.combine(week_start, datetime.min.time())
        ).count()
        
        goals[1]['current'] = week_journals
        goals[1]['progress'] = min(100, (week_journals / 3) * 100)
        
        # Weekly AI conversations (current week)
        week_chats = db.session.query(ChatMessage.session_id).filter_by(
            user_id=user_id,
            is_user_message=True
        ).filter(
            ChatMessage.timestamp >= datetime.combine(week_start, datetime.min.time())
        ).distinct().count()
        
        goals[2]['current'] = week_chats
        goals[2]['progress'] = min(100, (week_chats / 2) * 100)
        
        return jsonify({
            'goals': goals,
            'week_start': week_start.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get goals error: {str(e)}")
        return jsonify({'error': 'Failed to get goals'}), 500