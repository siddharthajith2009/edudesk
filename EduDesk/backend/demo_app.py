#!/usr/bin/env python3
"""
EduDesk Flask API Demo
This demonstrates the working API endpoints
"""

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime, timedelta

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'dev-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demo_edudesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'dev-jwt-secret-12345'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

# Simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# Simple Calendar Event model
class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start': self.start_time.isoformat(),
            'end': self.end_time.isoformat() if self.end_time else None,
            'allDay': self.all_day
        }

# API Routes
@app.route('/')
def hello():
    return '🎓 EduDesk Flask API is working!'

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'message': 'EduDesk API is running!',
        'endpoints': [
            'POST /api/auth/signup',
            'POST /api/auth/login',
            'GET /api/calendar/events',
            'POST /api/calendar/events'
        ]
    })

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('name', 'email', 'password')):
            return jsonify({'error': 'Name, email, and password are required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User(name=name, email=email, password_hash=password_hash)
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
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
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
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/calendar/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        user_id = get_jwt_identity()
        events = CalendarEvent.query.filter_by(user_id=user_id).all()
        return jsonify([event.to_dict() for event in events]), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/calendar/events', methods=['POST'])
@jwt_required()
def create_event():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Parse start time
        start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        end_time = None
        if data.get('end'):
            end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
        
        event = CalendarEvent(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            all_day=data.get('allDay', False)
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'message': 'Event created successfully',
            'event': event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
        print("✅ EduDesk Flask API is ready!")
        print("🚀 Starting server on http://localhost:5001")
        print("\n📋 Available endpoints:")
        print("  POST /api/auth/signup - User registration")
        print("  POST /api/auth/login - User login")
        print("  GET  /api/calendar/events - Get calendar events")
        print("  POST /api/calendar/events - Create calendar event")
        print("  GET  /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
