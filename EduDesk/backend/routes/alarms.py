from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Alarm
from datetime import datetime, time
import json

alarms_bp = Blueprint('alarms', __name__)

@alarms_bp.route('/alarms', methods=['GET'])
@jwt_required()
def get_alarms():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        is_active = request.args.get('active')
        
        # Build query
        query = Alarm.query.filter_by(user_id=user_id)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        alarms = query.order_by(Alarm.time).all()
        
        return jsonify([alarm.to_dict() for alarm in alarms]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get alarms error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/alarms', methods=['POST'])
@jwt_required()
def create_alarm():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('time'):
            return jsonify({'error': 'Title and time are required'}), 400
        
        title = data['title'].strip()
        if not title:
            return jsonify({'error': 'Title cannot be empty'}), 400
        
        # Parse time
        try:
            alarm_time = datetime.fromisoformat(data['time']).time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
        
        # Handle days of week
        days_of_week = data.get('days_of_week', [])
        if isinstance(days_of_week, list):
            days_json = json.dumps(days_of_week)
        else:
            days_json = json.dumps([])
        
        alarm = Alarm(
            user_id=user_id,
            title=title,
            time=alarm_time,
            days_of_week=days_json,
            is_active=data.get('is_active', True),
            sound=data.get('sound', 'default')
        )
        
        db.session.add(alarm)
        db.session.commit()
        
        return jsonify({
            'message': 'Alarm created successfully',
            'alarm': alarm.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create alarm error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/alarms/<int:alarm_id>', methods=['GET'])
@jwt_required()
def get_alarm(alarm_id):
    try:
        user_id = get_jwt_identity()
        alarm = Alarm.query.filter_by(id=alarm_id, user_id=user_id).first()
        
        if not alarm:
            return jsonify({'error': 'Alarm not found'}), 404
        
        return jsonify(alarm.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get alarm error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/alarms/<int:alarm_id>', methods=['PUT'])
@jwt_required()
def update_alarm(alarm_id):
    try:
        user_id = get_jwt_identity()
        alarm = Alarm.query.filter_by(id=alarm_id, user_id=user_id).first()
        
        if not alarm:
            return jsonify({'error': 'Alarm not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({'error': 'Title cannot be empty'}), 400
            alarm.title = title
        
        if 'time' in data:
            try:
                alarm.time = datetime.fromisoformat(data['time']).time()
            except ValueError:
                return jsonify({'error': 'Invalid time format'}), 400
        
        if 'days_of_week' in data:
            days_of_week = data['days_of_week']
            if isinstance(days_of_week, list):
                alarm.days_of_week = json.dumps(days_of_week)
            else:
                alarm.days_of_week = json.dumps([])
        
        if 'is_active' in data:
            alarm.is_active = data['is_active']
        
        if 'sound' in data:
            alarm.sound = data['sound']
        
        alarm.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Alarm updated successfully',
            'alarm': alarm.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update alarm error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/alarms/<int:alarm_id>', methods=['DELETE'])
@jwt_required()
def delete_alarm(alarm_id):
    try:
        user_id = get_jwt_identity()
        alarm = Alarm.query.filter_by(id=alarm_id, user_id=user_id).first()
        
        if not alarm:
            return jsonify({'error': 'Alarm not found'}), 404
        
        db.session.delete(alarm)
        db.session.commit()
        
        return jsonify({'message': 'Alarm deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete alarm error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/alarms/<int:alarm_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_alarm(alarm_id):
    try:
        user_id = get_jwt_identity()
        alarm = Alarm.query.filter_by(id=alarm_id, user_id=user_id).first()
        
        if not alarm:
            return jsonify({'error': 'Alarm not found'}), 404
        
        alarm.is_active = not alarm.is_active
        alarm.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if alarm.is_active else 'deactivated'
        return jsonify({
            'message': f'Alarm {status} successfully',
            'alarm': alarm.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle alarm error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_alarms():
    try:
        user_id = get_jwt_identity()
        current_time = datetime.utcnow().time()
        current_weekday = datetime.utcnow().weekday()
        
        # Get all active alarms
        alarms = Alarm.query.filter_by(user_id=user_id, is_active=True).all()
        
        upcoming_alarms = []
        
        for alarm in alarms:
            try:
                days_of_week = json.loads(alarm.days_of_week) if alarm.days_of_week else []
            except:
                days_of_week = []
            
            # Check if alarm should trigger today
            if not days_of_week or current_weekday in days_of_week:
                if alarm.time > current_time:
                    # Alarm is later today
                    upcoming_alarms.append({
                        'alarm': alarm.to_dict(),
                        'next_trigger': f"Today at {alarm.time.strftime('%H:%M')}"
                    })
                elif not days_of_week:
                    # One-time alarm that already passed
                    continue
                else:
                    # Find next occurrence
                    next_weekday = None
                    for day in sorted(days_of_week):
                        if day > current_weekday:
                            next_weekday = day
                            break
                    
                    if next_weekday is None:
                        # Next occurrence is next week
                        next_weekday = min(days_of_week)
                        days_ahead = 7 - current_weekday + next_weekday
                    else:
                        days_ahead = next_weekday - current_weekday
                    
                    upcoming_alarms.append({
                        'alarm': alarm.to_dict(),
                        'next_trigger': f"In {days_ahead} day(s) at {alarm.time.strftime('%H:%M')}"
                    })
        
        # Sort by next trigger time
        upcoming_alarms.sort(key=lambda x: x['alarm']['time'])
        
        return jsonify(upcoming_alarms), 200
        
    except Exception as e:
        current_app.logger.error(f"Get upcoming alarms error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@alarms_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_alarm_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total alarms
        total_alarms = Alarm.query.filter_by(user_id=user_id).count()
        
        # Get active alarms
        active_alarms = Alarm.query.filter_by(user_id=user_id, is_active=True).count()
        
        # Get inactive alarms
        inactive_alarms = total_alarms - active_alarms
        
        return jsonify({
            'total_alarms': total_alarms,
            'active_alarms': active_alarms,
            'inactive_alarms': inactive_alarms
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get alarm stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
