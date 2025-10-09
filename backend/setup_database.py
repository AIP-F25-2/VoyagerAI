#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for VoyagerAI
This script will create the database and tables for your VoyagerAI project
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the PostgreSQL database if it doesn't exist"""
    # Parse the DATABASE_URL to get connection details
    database_url = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/voyagerai')
    
    # Extract connection details
    if '://' in database_url:
        # Format: postgresql://user:pass@host:port/dbname
        parts = database_url.split('://')[1]
        if '@' in parts:
            auth, host_port_db = parts.split('@')
            user, password = auth.split(':')
            if '/' in host_port_db:
                host_port, dbname = host_port_db.split('/')
                if ':' in host_port:
                    host, port = host_port.split(':')
                else:
                    host, port = host_port, '5432'
            else:
                host, port, dbname = host_port_db, '5432', 'voyagerai'
        else:
            # No auth provided
            user, password = 'postgres', ''
            if '/' in parts:
                host_port, dbname = parts.split('/')
                if ':' in host_port:
                    host, port = host_port.split(':')
                else:
                    host, port = host_port, '5432'
            else:
                host, port, dbname = parts, '5432', 'voyagerai'
    else:
        print("❌ Invalid DATABASE_URL format")
        return False
    
    print(f"🔗 Connecting to PostgreSQL server at {host}:{port}")
    print(f"👤 User: {user}")
    print(f"🗄️  Target database: {dbname}")
    
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ Database '{dbname}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            print(f"✅ Database '{dbname}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_tables():
    """Create tables using Flask-SQLAlchemy"""
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Test database connection
            from app.models import Event
            event_count = Event.query.count()
            print(f"📊 Current events in database: {event_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up VoyagerAI PostgreSQL Database...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        return False
    
    print(f"📋 Using DATABASE_URL: {database_url}")
    print()
    
    # Step 1: Create database
    print("Step 1: Creating PostgreSQL database...")
    if not create_database():
        print("💥 Database creation failed!")
        return False
    
    print()
    
    # Step 2: Create tables
    print("Step 2: Creating database tables...")
    if not create_tables():
        print("💥 Table creation failed!")
        return False
    
    print()
    print("🎉 Database setup complete!")
    print()
    print("Next steps:")
    print("1. Update your .env file with correct PostgreSQL credentials")
    print("2. Start the Flask server: python wsgi.py")
    print("3. Test the API: GET http://localhost:5000/api/events")
    print("4. Scrape events: POST http://localhost:5000/api/scrape")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
