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
            # Check if we're using PostgreSQL
            database_url = os.getenv('DATABASE_URL', '')
            is_postgres = 'postgresql' in database_url or 'postgres' in database_url
            
            if is_postgres:
                print("📊 Detected PostgreSQL database")
                # For PostgreSQL, try to add missing columns first
                try:
                    from app.models import Hotel
                    # Test if the new columns exist by trying to query them
                    Hotel.query.count()
                except Exception as e:
                    if 'location' in str(e) or 'review_count' in str(e) or 'source' in str(e) or 'updated_at' in str(e):
                        print("🔄 Adding missing columns to existing hotel table...")
                        try:
                            # Add missing columns
                            with db.engine.connect() as conn:
                                conn.execute(db.text("ALTER TABLE hotel ADD COLUMN IF NOT EXISTS location VARCHAR(200)"))
                                conn.execute(db.text("ALTER TABLE hotel ADD COLUMN IF NOT EXISTS review_count INTEGER"))
                                conn.execute(db.text("ALTER TABLE hotel ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'csv'"))
                                conn.execute(db.text("ALTER TABLE hotel ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                                conn.commit()
                            print("✅ Added missing columns")
                        except Exception as col_error:
                            print(f"⚠️ Could not add columns: {col_error}")
                            print("🔄 Recreating hotel table...")
                            with db.engine.connect() as conn:
                                conn.execute(db.text("DROP TABLE IF EXISTS hotel CASCADE"))
                                conn.commit()
                            db.create_all()
                            print("✅ Hotel table recreated")
                    else:
                        raise e
            
            # Create all tables (this will create missing tables or skip existing ones)
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test database connection
            from app.models import Event, User, Hotel
            event_count = Event.query.count()
            user_count = User.query.count()
            hotel_count = Hotel.query.count()
            print(f"📊 Current events in database: {event_count}")
            print(f"👥 Current users in database: {user_count}")
            print(f"🏨 Current hotels in database: {hotel_count}")
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            print("💡 Try running: python migrate_db.py")
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
        print("1. Load hotels from CSV: python load_hotels_to_db.py")
        print("2. Start the Flask server: python wsgi.py")
        print("3. Scrape events: POST /api/scrape with city and limit")
        print("4. View events: GET /api/events")
        print("5. View hotels: GET /api/hotels")
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)
