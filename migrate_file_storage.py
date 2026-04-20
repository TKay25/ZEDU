#!/usr/bin/env python3
"""
Migration script to update course_materials.file_url column from VARCHAR(500) to TEXT
This allows storing large base64-encoded files
"""

import sys
from db_helper import get_db_connection

def migrate():
    print("=" * 70)
    print("ZEDU Database Migration: Expand file_url column")
    print("=" * 70)
    print()
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        print("🔄 Migrating course_materials.file_url from VARCHAR(500) to TEXT...")
        
        # Drop the old column constraint and recreate with TEXT type
        cursor.execute("""
            ALTER TABLE course_materials 
            ALTER COLUMN file_url TYPE TEXT;
        """)
        
        conn.commit()
        print("✅ Migration successful!")
        print()
        print("✨ The file_url column can now store large base64-encoded files")
        print("   - PDFs up to 50MB")
        print("   - Videos up to 500MB")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        print()
        print("If the table doesn't exist, it will be created with the correct")
        print("schema automatically when you next run init_db.py")
        sys.exit(1)
    finally:
        conn.close()
    
    print("=" * 70)

if __name__ == "__main__":
    migrate()
