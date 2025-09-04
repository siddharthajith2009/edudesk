from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import MoodEntry
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

mood_bp = Blueprint('mood', __name__)

# Mood configuration
MOOD_LEVELS = {
    'Happy': 9,
    'Neutral': 6,
    'Sad': 3,
    'Angry': 2,
    'Tired': 4,
    'Stressed': 2,
    'Excited': 8,
    'Anxious': 3,
    'Calm': 7,
    'Frustrated': 2
}

@mood_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_mood_entries():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = MoodEntry.query.filter_by(user_id=user_id)
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(MoodEntry.created_at >= start_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(MoodEntry.created_at <= end_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400
        
        entries = query.order_by(MoodEntry.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify([entry.to_dict() for entry in entries]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get mood entries error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/entries', methods=['POST'])
@jwt_required()
def create_mood_entry():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('mood'):
            return jsonify({'error': 'Mood is required'}), 400
        
        mood = data['mood']
        
        # Validate mood
        if mood not in MOOD_LEVELS:
            return jsonify({'error': 'Invalid mood type'}), 400
        
        # Get mood level
        mood_level = data.get('mood_level', MOOD_LEVELS[mood])
        
        # Check if user already has an entry for today
        today = datetime.utcnow().date()
        existing_entry = MoodEntry.query.filter(
            MoodEntry.user_id == user_id,
            db.func.date(MoodEntry.created_at) == today
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.mood = mood
            existing_entry.mood_level = mood_level
            existing_entry.notes = data.get('notes', '')
            existing_entry.created_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'message': 'Mood entry updated successfully',
                'entry': existing_entry.to_dict()
            }), 200
        else:
            # Create new entry
            entry = MoodEntry(
                user_id=user_id,
                mood=mood,
                mood_level=mood_level,
                notes=data.get('notes', '')
            )
            
            db.session.add(entry)
            db.session.commit()
            
            return jsonify({
                'message': 'Mood entry created successfully',
                'entry': entry.to_dict()
            }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create mood entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/entries/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_mood_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Mood entry not found'}), 404
        
        return jsonify(entry.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get mood entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_mood_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Mood entry not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'mood' in data:
            if data['mood'] not in MOOD_LEVELS:
                return jsonify({'error': 'Invalid mood type'}), 400
            entry.mood = data['mood']
        
        if 'mood_level' in data:
            entry.mood_level = data['mood_level']
        
        if 'notes' in data:
            entry.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Mood entry updated successfully',
            'entry': entry.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update mood entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_mood_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Mood entry not found'}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({'message': 'Mood entry deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete mood entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_mood_analytics():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get mood entries
        entries = MoodEntry.query.filter(
            MoodEntry.user_id == user_id,
            MoodEntry.created_at >= start_date
        ).order_by(MoodEntry.created_at).all()
        
        if not entries:
            return jsonify({
                'mood_distribution': {},
                'weekly_averages': {},
                'daily_moods': [],
                'mood_trend': [],
                'insights': []
            }), 200
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'mood': entry.mood,
            'mood_level': entry.mood_level,
            'date': entry.created_at.date(),
            'week': entry.created_at.isocalendar().week,
            'day_of_week': entry.created_at.strftime('%A')
        } for entry in entries])
        
        # Mood distribution
        mood_distribution = df['mood'].value_counts().to_dict()
        
        # Weekly averages
        weekly_averages = df.groupby('week')['mood_level'].mean().round(2).to_dict()
        
        # Daily moods (last 7 days)
        last_7_days = df.tail(7)
        daily_moods = [{
            'date': str(row['date']),
            'mood': row['mood'],
            'mood_level': row['mood_level']
        } for _, row in last_7_days.iterrows()]
        
        # Mood trend (7-day rolling average)
        df_sorted = df.sort_values('date')
        df_sorted['rolling_avg'] = df_sorted['mood_level'].rolling(window=7, min_periods=1).mean()
        mood_trend = [{
            'date': str(row['date']),
            'average_mood': round(row['rolling_avg'], 2)
        } for _, row in df_sorted.iterrows()]
        
        # Generate insights
        insights = []
        
        # Average mood level
        avg_mood = df['mood_level'].mean()
        insights.append(f"Your average mood level is {avg_mood:.1f}/10")
        
        # Most common mood
        most_common_mood = df['mood'].mode().iloc[0] if not df['mood'].mode().empty else None
        if most_common_mood:
            insights.append(f"Your most common mood is {most_common_mood}")
        
        # Mood trend analysis
        if len(df) >= 7:
            recent_avg = df.tail(7)['mood_level'].mean()
            older_avg = df.head(7)['mood_level'].mean()
            if recent_avg > older_avg + 0.5:
                insights.append("Your mood has been improving recently! 📈")
            elif recent_avg < older_avg - 0.5:
                insights.append("Your mood has been declining recently. Consider taking a break! 📉")
        
        # Day of week analysis
        day_analysis = df.groupby('day_of_week')['mood_level'].mean().sort_values(ascending=False)
        best_day = day_analysis.index[0]
        worst_day = day_analysis.index[-1]
        insights.append(f"You feel best on {best_day}s and worst on {worst_day}s")
        
        return jsonify({
            'mood_distribution': mood_distribution,
            'weekly_averages': weekly_averages,
            'daily_moods': daily_moods,
            'mood_trend': mood_trend,
            'insights': insights,
            'average_mood': round(avg_mood, 2),
            'total_entries': len(entries)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get mood analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_mood():
    try:
        user_id = get_jwt_identity()
        today = datetime.utcnow().date()
        
        entry = MoodEntry.query.filter(
            MoodEntry.user_id == user_id,
            db.func.date(MoodEntry.created_at) == today
        ).first()
        
        if entry:
            return jsonify(entry.to_dict()), 200
        else:
            return jsonify({'message': 'No mood entry for today'}), 404
        
    except Exception as e:
        current_app.logger.error(f"Get today mood error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@mood_bp.route('/streak', methods=['GET'])
@jwt_required()
def get_mood_streak():
    try:
        user_id = get_jwt_identity()
        
        # Get all mood entries ordered by date
        entries = MoodEntry.query.filter_by(user_id=user_id).order_by(MoodEntry.created_at.desc()).all()
        
        if not entries:
            return jsonify({'current_streak': 0, 'longest_streak': 0}), 200
        
        # Calculate current streak
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        current_date = datetime.utcnow().date()
        entry_dates = [entry.created_at.date() for entry in entries]
        
        # Check current streak
        for i, entry_date in enumerate(entry_dates):
            if i == 0:
                if entry_date == current_date or entry_date == current_date - timedelta(days=1):
                    current_streak = 1
                    temp_streak = 1
                else:
                    break
            else:
                if entry_date == entry_dates[i-1] - timedelta(days=1):
                    current_streak += 1
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return jsonify({
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get mood streak error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
