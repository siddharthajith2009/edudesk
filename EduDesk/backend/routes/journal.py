from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import JournalEntry
from datetime import datetime
import base64

journal_bp = Blueprint('journal', __name__)

def encode(text):
    """Simple base64 encoding for demo purposes"""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def decode(text):
    """Simple base64 decoding for demo purposes"""
    return base64.b64decode(text.encode('utf-8')).decode('utf-8')

@journal_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_journal_entries():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = JournalEntry.query.filter_by(user_id=user_id)
        
        if search:
            query = query.filter(JournalEntry.content.ilike(f'%{search}%'))
        
        entries = query.order_by(JournalEntry.created_at.desc()).offset(offset).limit(limit).all()
        
        # Decode encrypted entries
        result = []
        for entry in entries:
            entry_dict = entry.to_dict()
            if entry.is_encrypted:
                try:
                    entry_dict['content'] = decode(entry.content)
                except:
                    entry_dict['content'] = entry.content  # Fallback to original
            result.append(entry_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get journal entries error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/entries', methods=['POST'])
@jwt_required()
def create_journal_entry():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'error': 'Content is required'}), 400
        
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
        
        # Check if encryption is requested
        is_encrypted = data.get('is_encrypted', False)
        if is_encrypted:
            content = encode(content)
        
        entry = JournalEntry(
            user_id=user_id,
            content=content,
            mood=data.get('mood'),
            is_encrypted=is_encrypted
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Return decoded content for response
        response_data = entry.to_dict()
        if is_encrypted:
            response_data['content'] = data['content']  # Return original content
        
        return jsonify({
            'message': 'Journal entry created successfully',
            'entry': response_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create journal entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_journal_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        entry_dict = entry.to_dict()
        if entry.is_encrypted:
            try:
                entry_dict['content'] = decode(entry.content)
            except:
                entry_dict['content'] = entry.content
        
        return jsonify(entry_dict), 200
        
    except Exception as e:
        current_app.logger.error(f"Get journal entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_journal_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        data = request.get_json()
        
        if 'content' in data:
            content = data['content'].strip()
            if not content:
                return jsonify({'error': 'Content cannot be empty'}), 400
            
            # Handle encryption
            is_encrypted = data.get('is_encrypted', entry.is_encrypted)
            if is_encrypted:
                content = encode(content)
            
            entry.content = content
            entry.is_encrypted = is_encrypted
        
        if 'mood' in data:
            entry.mood = data['mood']
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Return decoded content for response
        response_data = entry.to_dict()
        if entry.is_encrypted and 'content' in data:
            response_data['content'] = data['content']  # Return original content
        
        return jsonify({
            'message': 'Journal entry updated successfully',
            'entry': response_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update journal entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_journal_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = JournalEntry.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({'error': 'Journal entry not found'}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({'message': 'Journal entry deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete journal entry error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/search', methods=['GET'])
@jwt_required()
def search_journal_entries():
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in content
        entries = JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.content.ilike(f'%{query}%')
        ).order_by(JournalEntry.created_at.desc()).all()
        
        # Decode encrypted entries for search results
        result = []
        for entry in entries:
            entry_dict = entry.to_dict()
            if entry.is_encrypted:
                try:
                    entry_dict['content'] = decode(entry.content)
                except:
                    entry_dict['content'] = entry.content
            result.append(entry_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Search journal entries error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@journal_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_journal_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total entries
        total_entries = JournalEntry.query.filter_by(user_id=user_id).count()
        
        # Get entries this month
        from datetime import datetime, timedelta
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_entries = JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= start_of_month
        ).count()
        
        # Get entries this week
        start_of_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_entries = JournalEntry.query.filter(
            JournalEntry.user_id == user_id,
            JournalEntry.created_at >= start_of_week
        ).count()
        
        # Get mood distribution
        mood_stats = db.session.query(
            JournalEntry.mood,
            db.func.count(JournalEntry.id)
        ).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.mood.isnot(None)
        ).group_by(JournalEntry.mood).all()
        
        mood_distribution = {mood: count for mood, count in mood_stats}
        
        return jsonify({
            'total_entries': total_entries,
            'monthly_entries': monthly_entries,
            'weekly_entries': weekly_entries,
            'mood_distribution': mood_distribution
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get journal stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
