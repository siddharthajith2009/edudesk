from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import StudySession
from datetime import datetime, timedelta
import pandas as pd

study_bp = Blueprint('study', __name__)

@study_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_study_sessions():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        subject = request.args.get('subject')
        session_type = request.args.get('session_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = StudySession.query.filter_by(user_id=user_id)
        
        if subject:
            query = query.filter(StudySession.subject.ilike(f'%{subject}%'))
        
        if session_type:
            query = query.filter_by(session_type=session_type)
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(StudySession.created_at >= start_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(StudySession.created_at <= end_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400
        
        sessions = query.order_by(StudySession.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify([session.to_dict() for session in sessions]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get study sessions error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_study_session():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('duration'):
            return jsonify({'error': 'Duration is required'}), 400
        
        duration = data['duration']
        if not isinstance(duration, int) or duration <= 0:
            return jsonify({'error': 'Duration must be a positive integer'}), 400
        
        session = StudySession(
            user_id=user_id,
            duration=duration,
            subject=data.get('subject'),
            notes=data.get('notes', ''),
            session_type=data.get('session_type', 'pomodoro')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Study session recorded successfully',
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create study session error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_study_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = StudySession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Study session not found'}), 404
        
        return jsonify(session.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get study session error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_study_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = StudySession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Study session not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'duration' in data:
            duration = data['duration']
            if not isinstance(duration, int) or duration <= 0:
                return jsonify({'error': 'Duration must be a positive integer'}), 400
            session.duration = duration
        
        if 'subject' in data:
            session.subject = data['subject']
        
        if 'notes' in data:
            session.notes = data['notes']
        
        if 'session_type' in data:
            session.session_type = data['session_type']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Study session updated successfully',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update study session error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_study_session(session_id):
    try:
        user_id = get_jwt_identity()
        session = StudySession.query.filter_by(id=session_id, user_id=user_id).first()
        
        if not session:
            return jsonify({'error': 'Study session not found'}), 404
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Study session deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete study session error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_study_analytics():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get study sessions
        sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.created_at >= start_date
        ).order_by(StudySession.created_at).all()
        
        if not sessions:
            return jsonify({
                'total_sessions': 0,
                'total_time': 0,
                'average_session': 0,
                'daily_breakdown': [],
                'subject_breakdown': {},
                'session_type_breakdown': {},
                'weekly_totals': [],
                'streak': 0
            }), 200
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'duration': session.duration,
            'subject': session.subject or 'Unknown',
            'session_type': session.session_type,
            'date': session.created_at.date(),
            'week': session.created_at.isocalendar().week
        } for session in sessions])
        
        # Basic stats
        total_sessions = len(sessions)
        total_time = df['duration'].sum()
        average_session = df['duration'].mean()
        
        # Daily breakdown
        daily_breakdown = df.groupby('date')['duration'].sum().reset_index()
        daily_breakdown['date'] = daily_breakdown['date'].astype(str)
        daily_breakdown = daily_breakdown.to_dict('records')
        
        # Subject breakdown
        subject_breakdown = df.groupby('subject')['duration'].sum().to_dict()
        
        # Session type breakdown
        session_type_breakdown = df.groupby('session_type')['duration'].sum().to_dict()
        
        # Weekly totals
        weekly_totals = df.groupby('week')['duration'].sum().reset_index()
        weekly_totals['week'] = weekly_totals['week'].astype(str)
        weekly_totals = weekly_totals.to_dict('records')
        
        # Calculate streak
        streak = calculate_study_streak(sessions)
        
        return jsonify({
            'total_sessions': total_sessions,
            'total_time': int(total_time),
            'average_session': round(average_session, 2),
            'daily_breakdown': daily_breakdown,
            'subject_breakdown': subject_breakdown,
            'session_type_breakdown': session_type_breakdown,
            'weekly_totals': weekly_totals,
            'streak': streak
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get study analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@study_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_study_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total sessions
        total_sessions = StudySession.query.filter_by(user_id=user_id).count()
        
        # Get total study time
        total_time = db.session.query(db.func.sum(StudySession.duration)).filter_by(user_id=user_id).scalar() or 0
        
        # Get sessions this week
        start_of_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.created_at >= start_of_week
        ).count()
        
        # Get sessions this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_sessions = StudySession.query.filter(
            StudySession.user_id == user_id,
            StudySession.created_at >= start_of_month
        ).count()
        
        # Get average session duration
        avg_duration = db.session.query(db.func.avg(StudySession.duration)).filter_by(user_id=user_id).scalar() or 0
        
        # Get most studied subject
        most_studied = db.session.query(
            StudySession.subject,
            db.func.sum(StudySession.duration)
        ).filter(
            StudySession.user_id == user_id,
            StudySession.subject.isnot(None)
        ).group_by(StudySession.subject).order_by(db.func.sum(StudySession.duration).desc()).first()
        
        most_studied_subject = most_studied[0] if most_studied else None
        
        return jsonify({
            'total_sessions': total_sessions,
            'total_time': int(total_time),
            'weekly_sessions': weekly_sessions,
            'monthly_sessions': monthly_sessions,
            'average_duration': round(avg_duration, 2),
            'most_studied_subject': most_studied_subject
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get study stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def calculate_study_streak(sessions):
    """Calculate current study streak in days"""
    if not sessions:
        return 0
    
    # Get unique dates
    dates = sorted(set(session.created_at.date() for session in sessions), reverse=True)
    
    if not dates:
        return 0
    
    # Calculate streak
    streak = 0
    current_date = datetime.utcnow().date()
    
    for i, date in enumerate(dates):
        if i == 0:
            # Check if most recent session was today or yesterday
            if date == current_date or date == current_date - timedelta(days=1):
                streak = 1
            else:
                break
        else:
            # Check if dates are consecutive
            if date == dates[i-1] - timedelta(days=1):
                streak += 1
            else:
                break
    
    return streak
