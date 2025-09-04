from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message
from app import db, bcrypt, mail
from models import User, PasswordReset
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('name', 'email', 'password')):
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate input
        if not name or len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].strip().lower()
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        # Always return success message for security (don't reveal if email exists)
        if user:
            # Generate secure token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Delete any existing reset tokens for this user
            PasswordReset.query.filter_by(user_id=user.id).delete()
            
            # Create new reset token
            reset_token = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset_token)
            db.session.commit()
            
            # Send email (if email service is configured)
            if current_app.config.get('MAIL_USERNAME'):
                try:
                    reset_link = f"{request.host_url}reset-password.html?token={token}"
                    msg = Message(
                        'Password Reset Request - EduDesk',
                        sender=current_app.config['MAIL_USERNAME'],
                        recipients=[email]
                    )
                    msg.html = f"""
                    <h2>Password Reset Request</h2>
                    <p>You requested a password reset for your EduDesk account.</p>
                    <p>Click the link below to reset your password:</p>
                    <a href="{reset_link}">Reset Password</a>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    """
                    mail.send(msg)
                except Exception as e:
                    current_app.logger.error(f"Email sending error: {str(e)}")
        
        return jsonify({
            'message': 'If this email is registered, a password reset link has been sent.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('token', 'password')):
            return jsonify({'error': 'Token and password are required'}), 400
        
        token = data['token']
        password = data['password']
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Find valid reset token
        reset_record = PasswordReset.query.filter_by(
            token=token,
            is_used=False
        ).first()
        
        if not reset_record or reset_record.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Update user password
        user = User.query.get(reset_record.user_id)
        if user:
            user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            reset_record.is_used = True
            
            db.session.commit()
            
            return jsonify({'message': 'Password reset successful'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reset password error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            name = data['name'].strip()
            if name and len(name) >= 2:
                user.name = name
            else:
                return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        
        if 'email' in data:
            email = data['email'].strip().lower()
            if validate_email(email):
                # Check if email is already taken by another user
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({'error': 'Email already in use'}), 409
                user.email = email
            else:
                return jsonify({'error': 'Invalid email format'}), 400
        
        if 'profile_picture' in data:
            user.profile_picture = data['profile_picture']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data or not all(k in data for k in ('current_password', 'new_password')):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verify current password
        if not bcrypt.check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
