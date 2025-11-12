#!/usr/bin/env python3
"""
Database migration script to add new columns to existing tables
Run this if you get column errors when initializing the database
"""

import os
import sys
from app import create_app
from app.models import db

def migrate_database():
    """Add new columns to existing tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting database migration...")
            
            # Check if we're using SQLite or PostgreSQL
            database_url = os.getenv('DATABASE_URL', '')
            is_postgres = 'postgresql' in database_url or 'postgres' in database_url
            
            if is_postgres:
                print("📊 Detected PostgreSQL database")
                # For PostgreSQL, we need to add columns if they don't exist
                try:
                    # Add location column if it doesn't exist
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE hotel 
                            ADD COLUMN IF NOT EXISTS location VARCHAR(200)
                        """))
                        conn.commit()
                    print("✅ Added location column")
                    
                    # Add review_count column if it doesn't exist
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE hotel 
                            ADD COLUMN IF NOT EXISTS review_count INTEGER
                        """))
                        conn.commit()
                    print("✅ Added review_count column")
                    
                    # Add source column if it doesn't exist
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE hotel 
                            ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'csv'
                        """))
                        conn.commit()
                    print("✅ Added source column")
                    
                    # Add updated_at column if it doesn't exist
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE hotel 
                            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        """))
                        conn.commit()
                    print("✅ Added updated_at column")
                    
                except Exception as e:
                    print(f"⚠️ PostgreSQL migration error: {e}")
                    print("Trying alternative approach...")
                    
                    # Alternative: Drop and recreate the table
                    print("🔄 Dropping and recreating hotel table...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text("DROP TABLE IF EXISTS hotel CASCADE"))
                        conn.commit()
                    db.create_all()
                    print("✅ Hotel table recreated")
                    
            else:
                print("📊 Detected SQLite database")
                # For SQLite, we need to recreate the table
                print("🔄 Recreating hotel table for SQLite...")
                
                # Drop the existing hotel table
                with db.engine.connect() as conn:
                    conn.execute(db.text("DROP TABLE IF EXISTS hotel"))
                    conn.commit()
                print("✅ Dropped existing hotel table")
                
                # Recreate all tables
                db.create_all()
                print("✅ Recreated all tables with new schema")
            
            # Test the migration
            from app.models import Hotel
            hotel_count = Hotel.query.count()
            print(f"✅ Migration successful! Hotel table now has {hotel_count} records")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 VoyagerAI Database Migration")
    print("This script will update your database schema to include new hotel columns.\n")
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now run:")
        print("  python init_db.py")
        print("  python load_hotels_to_db.py")
    else:
        print("\n💥 Migration failed!")
        print("You may need to manually drop and recreate the database.")
        sys.exit(1)
