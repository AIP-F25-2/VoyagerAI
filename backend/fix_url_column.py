#!/usr/bin/env python3
"""
Quick migration to fix URL column length issue
"""

import os
import sys
from app import create_app
from app.models import db

def fix_url_column():
    """Change URL column from VARCHAR(1000) to TEXT"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Fixing URL column length...")
            
            # Check if we're using PostgreSQL
            database_url = os.getenv('DATABASE_URL', '')
            is_postgres = 'postgresql' in database_url or 'postgres' in database_url
            
            if is_postgres:
                print("📊 Detected PostgreSQL database")
                with db.engine.connect() as conn:
                    # Change URL column to TEXT
                    conn.execute(db.text("ALTER TABLE hotel ALTER COLUMN url TYPE TEXT"))
                    conn.commit()
                print("✅ Changed URL column to TEXT")
            else:
                print("📊 Detected SQLite database")
                # SQLite doesn't support ALTER COLUMN, so we need to recreate
                print("🔄 Recreating hotel table for SQLite...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("DROP TABLE IF EXISTS hotel"))
                    conn.commit()
                db.create_all()
                print("✅ Hotel table recreated with TEXT URL column")
            
            print("✅ URL column fix completed!")
            return True
            
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Fixing Hotel URL Column Length")
    success = fix_url_column()
    
    if success:
        print("🎉 Fix completed successfully!")
    else:
        print("💥 Fix failed!")
        sys.exit(1)
