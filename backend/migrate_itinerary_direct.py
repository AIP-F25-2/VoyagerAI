#!/usr/bin/env python3
"""
Direct database migration script - doesn't require Flask
Uses psycopg2 for PostgreSQL or sqlite3 for SQLite directly
"""

import os
import sys

def migrate_postgresql(database_url):
    """Migrate PostgreSQL database"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse database URL
        parsed = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            user=parsed.username or 'postgres',
            password=parsed.password or '',
            database=parsed.path[1:] if parsed.path else 'voyagerai'
        )
        
        cur = conn.cursor()
        
        # Check and add is_shared column
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'itinerary' AND column_name = 'is_shared'
        """)
        if cur.fetchone() is None:
            cur.execute("ALTER TABLE itinerary ADD COLUMN is_shared BOOLEAN DEFAULT FALSE")
            print("✅ Added is_shared column")
        else:
            print("ℹ️  is_shared column already exists")
        
        # Check and add share_token column
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'itinerary' AND column_name = 'share_token'
        """)
        if cur.fetchone() is None:
            cur.execute("ALTER TABLE itinerary ADD COLUMN share_token VARCHAR(100)")
            print("✅ Added share_token column")
        else:
            print("ℹ️  share_token column already exists")
        
        # Check and create index
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname = 'idx_itinerary_share_token'
        """)
        if cur.fetchone() is None:
            cur.execute("""
                CREATE UNIQUE INDEX idx_itinerary_share_token 
                ON itinerary(share_token) 
                WHERE share_token IS NOT NULL
            """)
            print("✅ Created unique index on share_token")
        else:
            print("ℹ️  Index on share_token already exists")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Install it with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL migration failed: {e}")
        return False

def migrate_sqlite(database_url):
    """Migrate SQLite database"""
    try:
        import sqlite3
        
        # Extract database file path
        db_path = database_url.replace('sqlite:///', '').replace('sqlite://', '')
        if not db_path:
            db_path = 'voyagerai.db'
        
        if not os.path.exists(db_path):
            print(f"⚠️  Database file not found: {db_path}")
            print("Creating new database file...")
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Get existing columns
        cur.execute("PRAGMA table_info(itinerary)")
        columns = [row[1] for row in cur.fetchall()]
        
        # Add is_shared if it doesn't exist
        if 'is_shared' not in columns:
            cur.execute("ALTER TABLE itinerary ADD COLUMN is_shared BOOLEAN DEFAULT 0")
            print("✅ Added is_shared column")
        else:
            print("ℹ️  is_shared column already exists")
        
        # Add share_token if it doesn't exist
        if 'share_token' not in columns:
            cur.execute("ALTER TABLE itinerary ADD COLUMN share_token VARCHAR(100)")
            print("✅ Added share_token column")
        else:
            print("ℹ️  share_token column already exists")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite migration failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 VoyagerAI Itinerary Table Migration (Direct)")
    print("=" * 50)
    print("")
    
    # Load environment variables (try dotenv, but don't fail if not available)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available, use environment variables directly
    
    database_url = os.getenv('DATABASE_URL', 'sqlite:///voyagerai.db')
    
    print(f"Database URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    print("")
    
    if 'postgresql' in database_url or 'postgres' in database_url:
        success = migrate_postgresql(database_url)
    else:
        success = migrate_sqlite(database_url)
    
    if success:
        print("")
        print("🎉 Migration completed successfully!")
        print("You can now use group planning features.")
    else:
        print("")
        print("💥 Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

