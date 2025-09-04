from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import CalendarEvent
from datetime import datetime, timedelta
import json

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Build query
        query = CalendarEvent.query.filter_by(user_id=user_id)
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(CalendarEvent.start_time >= start_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(CalendarEvent.start_time <= end_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400
        
        events = query.order_by(CalendarEvent.start_time).all()
        
        return jsonify([event.to_dict() for event in events]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get events error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        if not data.get('start'):
            return jsonify({'error': 'Start time is required'}), 400
        
        # Parse start time
        try:
            start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start time format'}), 400
        
        # Parse end time if provided
        end_time = None
        if data.get('end'):
            try:
                end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end time format'}), 400
        
        # Create event
        event = CalendarEvent(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            all_day=data.get('allDay', False),
            background_color=data.get('backgroundColor', '#3b82f6'),
            border_color=data.get('borderColor', '#1d4ed8'),
            text_color=data.get('textColor', '#ffffff'),
            is_recurring=data.get('isRecurring', False),
            recurrence_type=data.get('recurrenceType'),
            recurrence_end=datetime.fromisoformat(data['recurrenceEnd'].replace('Z', '+00:00')) if data.get('recurrenceEnd') else None
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event': event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create event error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    try:
        user_id = get_jwt_identity()
        event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        return jsonify(event.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get event error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    try:
        user_id = get_jwt_identity()
        event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            event.title = data['title']
        
        if 'description' in data:
            event.description = data['description']
        
        if 'start' in data:
            try:
                event.start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start time format'}), 400
        
        if 'end' in data:
            if data['end']:
                try:
                    event.end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid end time format'}), 400
            else:
                event.end_time = None
        
        if 'allDay' in data:
            event.all_day = data['allDay']
        
        if 'backgroundColor' in data:
            event.background_color = data['backgroundColor']
        
        if 'borderColor' in data:
            event.border_color = data['borderColor']
        
        if 'textColor' in data:
            event.text_color = data['textColor']
        
        if 'isRecurring' in data:
            event.is_recurring = data['isRecurring']
        
        if 'recurrenceType' in data:
            event.recurrence_type = data['recurrenceType']
        
        if 'recurrenceEnd' in data:
            if data['recurrenceEnd']:
                try:
                    event.recurrence_end = datetime.fromisoformat(data['recurrenceEnd'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid recurrence end format'}), 400
            else:
                event.recurrence_end = None
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update event error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    try:
        user_id = get_jwt_identity()
        event = CalendarEvent.query.filter_by(id=event_id, user_id=user_id).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete event error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events/bulk', methods=['POST'])
@jwt_required()
def bulk_create_events():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'events' not in data:
            return jsonify({'error': 'Events array is required'}), 400
        
        events_data = data['events']
        created_events = []
        
        for event_data in events_data:
            if not event_data.get('title') or not event_data.get('start'):
                continue
            
            try:
                start_time = datetime.fromisoformat(event_data['start'].replace('Z', '+00:00'))
                end_time = None
                
                if event_data.get('end'):
                    end_time = datetime.fromisoformat(event_data['end'].replace('Z', '+00:00'))
                
                event = CalendarEvent(
                    user_id=user_id,
                    title=event_data['title'],
                    description=event_data.get('description', ''),
                    start_time=start_time,
                    end_time=end_time,
                    all_day=event_data.get('allDay', False),
                    background_color=event_data.get('backgroundColor', '#3b82f6'),
                    border_color=event_data.get('borderColor', '#1d4ed8'),
                    text_color=event_data.get('textColor', '#ffffff')
                )
                
                db.session.add(event)
                created_events.append(event)
                
            except ValueError:
                continue
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(created_events)} events created successfully',
            'events': [event.to_dict() for event in created_events]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk create events error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@calendar_bp.route('/events/search', methods=['GET'])
@jwt_required()
def search_events():
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in title and description
        events = CalendarEvent.query.filter(
            CalendarEvent.user_id == user_id,
            (CalendarEvent.title.ilike(f'%{query}%') | 
             CalendarEvent.description.ilike(f'%{query}%'))
        ).order_by(CalendarEvent.start_time).all()
        
        return jsonify([event.to_dict() for event in events]), 200
        
    except Exception as e:
        current_app.logger.error(f"Search events error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
