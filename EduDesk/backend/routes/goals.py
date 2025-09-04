from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Goal
from datetime import datetime, date

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/goals', methods=['GET'])
@jwt_required()
def get_goals():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        category = request.args.get('category')
        priority = request.args.get('priority')
        
        # Build query
        query = Goal.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(category=category)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        goals = query.order_by(Goal.created_at.desc()).all()
        
        return jsonify([goal.to_dict() for goal in goals]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get goals error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/goals', methods=['POST'])
@jwt_required()
def create_goal():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        title = data['title'].strip()
        if not title:
            return jsonify({'error': 'Title cannot be empty'}), 400
        
        # Parse target date if provided
        target_date = None
        if data.get('target_date'):
            try:
                target_date = datetime.fromisoformat(data['target_date']).date()
            except ValueError:
                return jsonify({'error': 'Invalid target date format'}), 400
        
        goal = Goal(
            user_id=user_id,
            title=title,
            description=data.get('description', ''),
            target_date=target_date,
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'active'),
            progress=data.get('progress', 0),
            category=data.get('category')
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'message': 'Goal created successfully',
            'goal': goal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create goal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/goals/<int:goal_id>', methods=['GET'])
@jwt_required()
def get_goal(goal_id):
    try:
        user_id = get_jwt_identity()
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
        
        return jsonify(goal.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get goal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/goals/<int:goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    try:
        user_id = get_jwt_identity()
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({'error': 'Title cannot be empty'}), 400
            goal.title = title
        
        if 'description' in data:
            goal.description = data['description']
        
        if 'target_date' in data:
            if data['target_date']:
                try:
                    goal.target_date = datetime.fromisoformat(data['target_date']).date()
                except ValueError:
                    return jsonify({'error': 'Invalid target date format'}), 400
            else:
                goal.target_date = None
        
        if 'priority' in data:
            if data['priority'] in ['low', 'medium', 'high']:
                goal.priority = data['priority']
            else:
                return jsonify({'error': 'Invalid priority level'}), 400
        
        if 'status' in data:
            if data['status'] in ['active', 'completed', 'cancelled']:
                goal.status = data['status']
            else:
                return jsonify({'error': 'Invalid status'}), 400
        
        if 'progress' in data:
            progress = data['progress']
            if isinstance(progress, int) and 0 <= progress <= 100:
                goal.progress = progress
            else:
                return jsonify({'error': 'Progress must be between 0 and 100'}), 400
        
        if 'category' in data:
            goal.category = data['category']
        
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Goal updated successfully',
            'goal': goal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update goal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    try:
        user_id = get_jwt_identity()
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
        
        db.session.delete(goal)
        db.session.commit()
        
        return jsonify({'message': 'Goal deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete goal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/goals/<int:goal_id>/progress', methods=['PUT'])
@jwt_required()
def update_goal_progress(goal_id):
    try:
        user_id = get_jwt_identity()
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
        
        data = request.get_json()
        
        if 'progress' not in data:
            return jsonify({'error': 'Progress is required'}), 400
        
        progress = data['progress']
        if not isinstance(progress, int) or not 0 <= progress <= 100:
            return jsonify({'error': 'Progress must be between 0 and 100'}), 400
        
        goal.progress = progress
        
        # Auto-complete if progress is 100%
        if progress == 100 and goal.status == 'active':
            goal.status = 'completed'
        
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Goal progress updated successfully',
            'goal': goal.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update goal progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_goals_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total goals
        total_goals = Goal.query.filter_by(user_id=user_id).count()
        
        # Get goals by status
        active_goals = Goal.query.filter_by(user_id=user_id, status='active').count()
        completed_goals = Goal.query.filter_by(user_id=user_id, status='completed').count()
        cancelled_goals = Goal.query.filter_by(user_id=user_id, status='cancelled').count()
        
        # Get goals by priority
        high_priority = Goal.query.filter_by(user_id=user_id, priority='high').count()
        medium_priority = Goal.query.filter_by(user_id=user_id, priority='medium').count()
        low_priority = Goal.query.filter_by(user_id=user_id, priority='low').count()
        
        # Get completion rate
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Get overdue goals
        today = date.today()
        overdue_goals = Goal.query.filter(
            Goal.user_id == user_id,
            Goal.status == 'active',
            Goal.target_date < today
        ).count()
        
        return jsonify({
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'cancelled_goals': cancelled_goals,
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'completion_rate': round(completion_rate, 2),
            'overdue_goals': overdue_goals
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get goals stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@goals_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_goal_categories():
    try:
        user_id = get_jwt_identity()
        
        # Get unique categories
        categories = db.session.query(Goal.category).filter(
            Goal.user_id == user_id,
            Goal.category.isnot(None)
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get goal categories error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
