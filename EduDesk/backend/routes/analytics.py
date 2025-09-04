from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, CalendarEvent, MoodEntry, JournalEntry, Goal, StudySession, BlogPost, Alarm, UserDocument
from datetime import datetime, timedelta
import pandas as pd

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_analytics():
    try:
        user_id = get_jwt_identity()
        
        # Get basic counts
        total_events = CalendarEvent.query.filter_by(user_id=user_id).count()
        total_mood_entries = MoodEntry.query.filter_by(user_id=user_id).count()
        total_journal_entries = JournalEntry.query.filter_by(user_id=user_id).count()
        total_goals = Goal.query.filter_by(user_id=user_id).count()
        total_study_sessions = StudySession.query.filter_by(user_id=user_id).count()
        total_blog_posts = BlogPost.query.filter_by(user_id=user_id).count()
        total_alarms = Alarm.query.filter_by(user_id=user_id).count()
        total_documents = UserDocument.query.filter_by(user_id=user_id).count()
        
        # Get recent activity (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        recent_events = CalendarEvent.query.filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.created_at >= recent_date
        ).count()
        
        recent_mood_entries = MoodEntry.query.filter(
            MoodEntry.user_id == user_id,
            MoodEntry.created_at >= recent_date
        ).count()
        
        recent_journal_entries = JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= recent_date
        ).count()
        
        recent_study_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.created_at >= recent_date
        ).count()
        
        # Get goal completion rate
        completed_goals = Goal.query.filter_by(user_id=user_id, status='completed').count()
        goal_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Get total study time
        total_study_time = db.session.query(db.func.sum(StudySession.duration)).filter_by(user_id=user_id).scalar() or 0
        
        return jsonify({
            'overview': {
                'total_events': total_events,
                'total_mood_entries': total_mood_entries,
                'total_journal_entries': total_journal_entries,
                'total_goals': total_goals,
                'total_study_sessions': total_study_sessions,
                'total_blog_posts': total_blog_posts,
                'total_alarms': total_alarms,
                'total_documents': total_documents
            },
            'recent_activity': {
                'events': recent_events,
                'mood_entries': recent_mood_entries,
                'journal_entries': recent_journal_entries,
                'study_sessions': recent_study_sessions
            },
            'achievements': {
                'goal_completion_rate': round(goal_completion_rate, 2),
                'total_study_time': int(total_study_time)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get dashboard analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/productivity', methods=['GET'])
@jwt_required()
def get_productivity_analytics():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get study sessions
        study_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.created_at >= start_date
        ).all()
        
        # Get goals
        goals = Goal.query.filter(
            Goal.user_id == user_id,
            Goal.created_at >= start_date
        ).all()
        
        # Get calendar events
        events = CalendarEvent.query.filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_date
        ).all()
        
        # Calculate productivity metrics
        total_study_time = sum(session.duration for session in study_sessions)
        avg_study_session = total_study_time / len(study_sessions) if study_sessions else 0
        
        completed_goals = len([g for g in goals if g.status == 'completed'])
        goal_completion_rate = (completed_goals / len(goals) * 100) if goals else 0
        
        # Daily productivity breakdown
        daily_data = {}
        for session in study_sessions:
            date = session.created_at.date()
            if date not in daily_data:
                daily_data[date] = {'study_time': 0, 'sessions': 0, 'goals_completed': 0}
            daily_data[date]['study_time'] += session.duration
            daily_data[date]['sessions'] += 1
        
        for goal in goals:
            if goal.status == 'completed':
                date = goal.updated_at.date()
                if date not in daily_data:
                    daily_data[date] = {'study_time': 0, 'sessions': 0, 'goals_completed': 0}
                daily_data[date]['goals_completed'] += 1
        
        # Convert to list format
        daily_breakdown = []
        for date, data in sorted(daily_data.items()):
            daily_breakdown.append({
                'date': str(date),
                'study_time': data['study_time'],
                'sessions': data['sessions'],
                'goals_completed': data['goals_completed']
            })
        
        return jsonify({
            'total_study_time': int(total_study_time),
            'average_session_duration': round(avg_study_session, 2),
            'goal_completion_rate': round(goal_completion_rate, 2),
            'daily_breakdown': daily_breakdown
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get productivity analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
