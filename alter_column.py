#!/usr/bin/env python3
"""
Direct SQL: Alter course_materials.file_url column from VARCHAR(500) to TEXT
Run this script to execute the migration
"""

import sys
from db_helper import get_db_connection

def main():
    print("=" * 70)
    print("ZEDU Database Migration: Alter file_url Column")
    print("=" * 70)
    print()
    
    conn = get_db_connection()
    if not conn:
        print("[ERROR] Failed to connect to database")
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        print("[INFO] Executing SQL: ALTER TABLE course_materials ALTER COLUMN file_url TYPE TEXT;")
        print()
        
        # Execute the ALTER TABLE command
        cursor.execute("""
            ALTER TABLE course_materials 
            ALTER COLUMN file_url TYPE TEXT;
        """)
        
        conn.commit()
        print("[SUCCESS] Migration successful!")
        print()
        print("[INFO] The file_url column can now store large base64-encoded files")
        print("   - PDFs up to 50MB")
        print("   - Videos up to 500MB")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {str(e)}")
        print()
        if "does not exist" in str(e).lower():
            print("[INFO] The table may not exist yet.")
            print("[INFO] Run: python init_db.py")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
    
    print("=" * 70)

if __name__ == "__main__":
    main()
