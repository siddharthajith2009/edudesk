#!/usr/bin/env python3
"""
Simple test script to check Flask app setup
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create Flask app
app = Flask(__name__)

# Set configuration directly
app.config['SECRET_KEY'] = 'dev-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_edudesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Simple test model
class TestUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Test route
@app.route('/')
def hello():
    return 'Hello! EduDesk Flask API is working!'

@app.route('/api/health')
def health():
    return {'status': 'healthy', 'message': 'EduDesk API is running!'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
        print("✅ Flask app is ready!")
    
    print("🚀 Starting Flask development server on http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
