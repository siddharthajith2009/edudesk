from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from models import UserDocument
import os
import uuid
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
    'mp3', 'wav', 'ogg', 'mp4', 'avi', 'mov',
    'zip', 'rar', '7z', 'tar', 'gz',
    'xls', 'xlsx', 'csv', 'ppt', 'pptx'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    extension = filename.rsplit('.', 1)[1].lower()
    if extension in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']:
        return 'document'
    elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
        return 'image'
    elif extension in ['mp3', 'wav', 'ogg', 'mp4', 'avi', 'mov']:
        return 'media'
    elif extension in ['zip', 'rar', '7z', 'tar', 'gz']:
        return 'archive'
    elif extension in ['xls', 'xlsx', 'csv', 'ppt', 'pptx']:
        return 'spreadsheet'
    else:
        return 'other'

@documents_bp.route('/documents', methods=['GET'])
@jwt_required()
def get_documents():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        category = request.args.get('category')
        file_type = request.args.get('file_type')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = UserDocument.query.filter_by(user_id=user_id)
        
        if category:
            query = query.filter_by(category=category)
        
        if file_type:
            query = query.filter_by(file_type=file_type)
        
        documents = query.order_by(UserDocument.uploaded_at.desc()).offset(offset).limit(limit).all()
        
        return jsonify([doc.to_dict() for doc in documents]), 200
        
    except Exception as e:
        current_app.logger.error(f"Get documents error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get file type
        file_type = get_file_type(original_filename)
        
        # Create database record
        document = UserDocument(
            user_id=user_id,
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            category=request.form.get('category', 'general')
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/documents/<int:document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    try:
        user_id = get_jwt_identity()
        document = UserDocument.query.filter_by(id=document_id, user_id=user_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify(document.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f"Get document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/documents/<int:document_id>', methods=['PUT'])
@jwt_required()
def update_document(document_id):
    try:
        user_id = get_jwt_identity()
        document = UserDocument.query.filter_by(id=document_id, user_id=user_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'category' in data:
            document.category = data['category']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': document.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/documents/<int:document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    try:
        user_id = get_jwt_identity()
        document = UserDocument.query.filter_by(id=document_id, user_id=user_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete file from filesystem
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            current_app.logger.warning(f"Could not delete file {document.file_path}: {str(e)}")
        
        # Delete database record
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/download/<int:document_id>', methods=['GET'])
@jwt_required()
def download_document(document_id):
    try:
        user_id = get_jwt_identity()
        document = UserDocument.query.filter_by(id=document_id, user_id=user_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        from flask import send_file
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Download document error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_document_categories():
    try:
        user_id = get_jwt_identity()
        
        # Get unique categories
        categories = db.session.query(UserDocument.category).filter(
            UserDocument.user_id == user_id,
            UserDocument.category.isnot(None)
        ).distinct().all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get document categories error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@documents_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_document_stats():
    try:
        user_id = get_jwt_identity()
        
        # Get total documents
        total_documents = UserDocument.query.filter_by(user_id=user_id).count()
        
        # Get total file size
        total_size = db.session.query(db.func.sum(UserDocument.file_size)).filter_by(user_id=user_id).scalar() or 0
        
        # Get documents by type
        type_stats = db.session.query(
            UserDocument.file_type,
            db.func.count(UserDocument.id),
            db.func.sum(UserDocument.file_size)
        ).filter_by(user_id=user_id).group_by(UserDocument.file_type).all()
        
        type_breakdown = {}
        for file_type, count, size in type_stats:
            type_breakdown[file_type] = {
                'count': count,
                'total_size': int(size) if size else 0
            }
        
        # Get recent uploads (last 7 days)
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_uploads = UserDocument.query.filter(
            UserDocument.user_id == user_id,
            UserDocument.uploaded_at >= recent_date
        ).count()
        
        return jsonify({
            'total_documents': total_documents,
            'total_size': int(total_size),
            'type_breakdown': type_breakdown,
            'recent_uploads': recent_uploads
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get document stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
