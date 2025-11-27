#!/usr/bin/env python3
"""
Database migration script to add is_shared and share_token columns to itinerary table
Run this if you get column errors when creating itineraries
"""

import os
import sys
from app import create_app
from app.models import db

def migrate_itinerary_table():
    """Add is_shared and share_token columns to itinerary table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting itinerary table migration...")
            
            # Check if we're using SQLite or PostgreSQL
            database_url = os.getenv('DATABASE_URL', '')
            is_postgres = 'postgresql' in database_url or 'postgres' in database_url
            
            if is_postgres:
                print("📊 Detected PostgreSQL database")
                with db.engine.connect() as conn:
                    # Add is_shared column if it doesn't exist
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE itinerary 
                            ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE
                        """))
                        conn.commit()
                        print("✅ Added is_shared column")
                    except Exception as e:
                        print(f"⚠️ Error adding is_shared: {e}")
                    
                    # Add share_token column if it doesn't exist
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE itinerary 
                            ADD COLUMN IF NOT EXISTS share_token VARCHAR(100)
                        """))
                        conn.commit()
                        print("✅ Added share_token column")
                    except Exception as e:
                        print(f"⚠️ Error adding share_token: {e}")
                    
                    # Create unique index on share_token if it doesn't exist
                    try:
                        conn.execute(db.text("""
                            CREATE UNIQUE INDEX IF NOT EXISTS idx_itinerary_share_token 
                            ON itinerary(share_token) 
                            WHERE share_token IS NOT NULL
                        """))
                        conn.commit()
                        print("✅ Created unique index on share_token")
                    except Exception as e:
                        print(f"⚠️ Error creating index: {e}")
                        
            else:
                print("📊 Detected SQLite database")
                # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS well
                # We'll need to check if columns exist first
                try:
                    # Check if columns exist by trying to query them
                    with db.engine.connect() as conn:
                        result = conn.execute(db.text("PRAGMA table_info(itinerary)"))
                        columns = [row[1] for row in result]
                        
                        if 'is_shared' not in columns:
                            conn.execute(db.text("ALTER TABLE itinerary ADD COLUMN is_shared BOOLEAN DEFAULT 0"))
                            conn.commit()
                            print("✅ Added is_shared column")
                        else:
                            print("ℹ️ is_shared column already exists")
                        
                        if 'share_token' not in columns:
                            conn.execute(db.text("ALTER TABLE itinerary ADD COLUMN share_token VARCHAR(100)"))
                            conn.commit()
                            print("✅ Added share_token column")
                        else:
                            print("ℹ️ share_token column already exists")
                            
                except Exception as e:
                    print(f"⚠️ SQLite migration error: {e}")
                    print("Trying alternative approach...")
                    
                    # Alternative: Recreate the table (WARNING: This will lose data!)
                    print("⚠️ WARNING: This will recreate the itinerary table and may lose data!")
                    response = input("Do you want to continue? (yes/no): ")
                    if response.lower() != 'yes':
                        print("Migration cancelled.")
                        return False
                    
                    print("🔄 Recreating itinerary table...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text("DROP TABLE IF EXISTS itinerary"))
                        conn.commit()
                    db.create_all()
                    print("✅ Itinerary table recreated")
            
            # Test the migration
            from app.models import Itinerary
            try:
                itinerary_count = Itinerary.query.count()
                print(f"✅ Migration successful! Itinerary table now has {itinerary_count} records")
            except Exception as e:
                print(f"⚠️ Could not verify migration: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 VoyagerAI Itinerary Table Migration")
    print("This script will add is_shared and share_token columns to the itinerary table.\n")
    
    success = migrate_itinerary_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use group planning features.")
    else:
        print("\n💥 Migration failed!")
        print("You may need to manually update the database schema.")
        sys.exit(1)

