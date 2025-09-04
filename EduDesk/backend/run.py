#!/usr/bin/env python3
"""
EduDesk Flask Backend
Run this file to start the development server
"""

from app import app, db

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created successfully!")
    
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5001)
