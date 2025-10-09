#!/usr/bin/env python3
"""
Database Management Script for VoyagerAI
Provides utilities for database operations
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    try:
        from app import create_app
        from app.models import db, Event
        
        app = create_app()
        
        with app.app_context():
            # Test basic connection
            result = db.session.execute(db.text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Test table access
            event_count = Event.query.count()
            print(f"📊 Events in database: {event_count}")
            
            # Test database info
            db_info = db.session.execute(db.text("SELECT version()")).scalar()
            print(f"🗄️  Database version: {db_info}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def add_sample_event():
    """Add a sample event to test the database"""
    try:
        from app import create_app
        from app.models import db, Event
        
        app = create_app()
        
        with app.app_context():
            # Create sample event
            sample_event = Event(
                title="Sample Concert Event",
                venue="Sample Venue",
                place="Sample City",
                price="₹500-₹2000",
                url="https://example.com/event",
                city="Mumbai"
            )
            
            db.session.add(sample_event)
            db.session.commit()
            
            print("✅ Sample event added successfully")
            print(f"📝 Event ID: {sample_event.id}")
            print(f"📝 Event Title: {sample_event.title}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error adding sample event: {e}")
        return False

def list_events():
    """List all events in the database"""
    try:
        from app import create_app
        from app.models import db, Event
        
        app = create_app()
        
        with app.app_context():
            events = Event.query.all()
            
            if not events:
                print("📭 No events found in database")
                return True
            
            print(f"📋 Found {len(events)} events:")
            print("-" * 80)
            
            for event in events:
                print(f"ID: {event.id}")
                print(f"Title: {event.title}")
                print(f"Venue: {event.venue}")
                print(f"City: {event.city}")
                print(f"Price: {event.price}")
                print(f"Created: {event.created_at}")
                print("-" * 80)
            
            return True
            
    except Exception as e:
        print(f"❌ Error listing events: {e}")
        return False

def clear_events():
    """Clear all events from the database"""
    try:
        from app import create_app
        from app.models import db, Event
        
        app = create_app()
        
        with app.app_context():
            count = Event.query.count()
            Event.query.delete()
            db.session.commit()
            
            print(f"🗑️  Deleted {count} events from database")
            return True
            
    except Exception as e:
        print(f"❌ Error clearing events: {e}")
        return False

def show_database_info():
    """Show database configuration and status"""
    database_url = os.getenv('DATABASE_URL', 'Not set')
    
    print("🗄️  Database Configuration:")
    print(f"   DATABASE_URL: {database_url}")
    
    if 'postgresql' in database_url:
        print("   Type: PostgreSQL")
    elif 'sqlite' in database_url:
        print("   Type: SQLite")
    else:
        print("   Type: Unknown")
    
    print()

def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("VoyagerAI Database Manager")
        print("=" * 30)
        print("Usage: python db_manager.py <command>")
        print()
        print("Commands:")
        print("  test     - Test database connection")
        print("  info     - Show database configuration")
        print("  sample   - Add a sample event")
        print("  list     - List all events")
        print("  clear    - Clear all events")
        print("  setup    - Run full database setup")
        return
    
    command = sys.argv[1].lower()
    
    print(f"🔧 Running command: {command}")
    print()
    
    if command == "test":
        show_database_info()
        test_connection()
    elif command == "info":
        show_database_info()
    elif command == "sample":
        add_sample_event()
    elif command == "list":
        list_events()
    elif command == "clear":
        confirm = input("Are you sure you want to clear all events? (y/N): ")
        if confirm.lower() == 'y':
            clear_events()
        else:
            print("❌ Operation cancelled")
    elif command == "setup":
        show_database_info()
        if test_connection():
            print("✅ Database is ready!")
        else:
            print("❌ Database setup failed!")
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
