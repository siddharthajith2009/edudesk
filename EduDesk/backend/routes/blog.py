from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import BlogPost
from datetime import datetime
import json

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/posts', methods=['GET'])
@jwt_required()
def get_blog_posts():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        is_public = request.args.get('public')
        search = request.args.get('search', '').strip()
        
        # Build query
        query = BlogPost.query.filter_by(user_id=user_id)
        
        if is_public is not None:
            query = query.filter_by(is_public=is_public.lower() == 'true')
        
        if search:
            query = query.filter(
                (BlogPost.title.ilike(f'%{search}%')) | 
                (BlogPost.content.ilike(f'%{search}%'))
            )
        
        posts = query.order_by(BlogPost.created_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify([post.to_dict() for post in posts]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get blog posts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/posts', methods=['POST'])
@jwt_required()
def create_blog_post():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400
        
        title = data['title'].strip()
        content = data['content'].strip()
        
        if not title or not content:
            return jsonify({'error': 'Title and content cannot be empty'}), 400
        
        # Handle tags
        tags = data.get('tags', [])
        if isinstance(tags, list):
            tags_json = json.dumps(tags)
        else:
            tags_json = json.dumps([])
        
        post = BlogPost(
            user_id=user_id,
            title=title,
            content=content,
            tags=tags_json,
            is_public=data.get('is_public', False)
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Blog post created successfully',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create blog post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_blog_post(post_id):
    try:
        user_id = get_jwt_identity()
        post = BlogPost.query.filter_by(id=post_id, user_id=user_id).first()
        
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        
        return jsonify(post.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get blog post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_blog_post(post_id):
    try:
        user_id = get_jwt_identity()
        post = BlogPost.query.filter_by(id=post_id, user_id=user_id).first()
        
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({'error': 'Title cannot be empty'}), 400
            post.title = title
        
        if 'content' in data:
            content = data['content'].strip()
            if not content:
                return jsonify({'error': 'Content cannot be empty'}), 400
            post.content = content
        
        if 'tags' in data:
            tags = data['tags']
            if isinstance(tags, list):
                post.tags = json.dumps(tags)
            else:
                post.tags = json.dumps([])
        
        if 'is_public' in data:
            post.is_public = data['is_public']
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Blog post updated successfully',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update blog post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_blog_post(post_id):
    try:
        user_id = get_jwt_identity()
        post = BlogPost.query.filter_by(id=post_id, user_id=user_id).first()
        
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Blog post deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete blog post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/posts/<int:post_id>/publish', methods=['PUT'])
@jwt_required()
def toggle_blog_post_visibility(post_id):
    try:
        user_id = get_jwt_identity()
        post = BlogPost.query.filter_by(id=post_id, user_id=user_id).first()
        
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        
        post.is_public = not post.is_public
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'published' if post.is_public else 'unpublished'
        return jsonify({
            'message': f'Blog post {status} successfully',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle blog post visibility error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/public', methods=['GET'])
def get_public_posts():
    try:
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query for public posts only
        query = BlogPost.query.filter_by(is_public=True)
        
        if search:
            query = query.filter(
                (BlogPost.title.ilike(f'%{search}%')) | 
                (BlogPost.content.ilike(f'%{search}%'))
            )
        
        posts = query.order_by(BlogPost.created_at.desc()).offset(offset).limit(limit).all()
        
        # Return posts with user info but without sensitive data
        result = []
        for post in posts:
            post_dict = post.to_dict()
            post_dict['author'] = post.user.name
            result.append(post_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Get public blog posts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_blog_tags():
    try:
        user_id = get_jwt_identity()
        
        # Get all tags from user's posts
        posts = BlogPost.query.filter_by(user_id=user_id).all()
        
        all_tags = []
        for post in posts:
            if post.tags:
                try:
                    tags = json.loads(post.tags)
                    all_tags.extend(tags)
                except:
                    continue
        
        # Get unique tags with counts
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return jsonify({'tags': tag_counts}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get blog tags error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@blog_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_blog_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total posts
        total_posts = BlogPost.query.filter_by(user_id=user_id).count()
        
        # Get public posts
        public_posts = BlogPost.query.filter_by(user_id=user_id, is_public=True).count()
        
        # Get posts this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_posts = BlogPost.query.filter(
            BlogPost.user_id == user_id,
            BlogPost.created_at >= start_of_month
        ).count()
        
        return jsonify({
            'total_posts': total_posts,
            'public_posts': public_posts,
            'private_posts': total_posts - public_posts,
            'monthly_posts': monthly_posts
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get blog stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
