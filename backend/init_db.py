#!/usr/bin/env python3
"""
Database initialization script for VoyagerAI
Run this to create the database and tables
"""

import os
import sys
from app import create_app
from app.models import db

def init_database():
    """Initialize the database with tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test database connection
            from app.models import Event
            event_count = Event.query.count()
            print(f"📊 Current events in database: {event_count}")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Initializing VoyagerAI Database (SQLite by default)...")
    
    if not os.getenv('DATABASE_URL'):
        print("ℹ️  Using SQLite at voyagerai.db. To use Postgres later, set DATABASE_URL.")
    
    success = init_database()
    
    if success:
        print("🎉 Database initialization complete!")
        print("\nNext steps:")
        print("1. Start the Flask server: python wsgi.py")
        print("2. Scrape events: POST /api/scrape with city and limit")
        print("3. View events: GET /api/events")
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)
