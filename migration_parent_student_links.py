#!/usr/bin/env python3
"""
Migration script to add parent-student linking table and functions to ZEDU database
Run this once to set up the parent-student account linking system
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://zeduweb_user:qdEe6bfJmlIHAknO2TVbum3SSm2kFvFV@dpg-d7cklfa8qa3s73e9podg-a.oregon-postgres.render.com/zeduweb"

def run_migration():
    """Run the migration to add parent-student linking table"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create parent_student_links table
        print("Creating parent_student_links table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_student_links (
                id SERIAL PRIMARY KEY,
                parent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                relationship_type VARCHAR(50) DEFAULT 'parent' CHECK (relationship_type IN ('parent', 'guardian', 'custodian')),
                status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                verification_code VARCHAR(10),
                approval_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for better query performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_links_parent ON parent_student_links(parent_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_links_student ON parent_student_links(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_links_status ON parent_student_links(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parent_links_code ON parent_student_links(verification_code);")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.errors.DuplicateTable:
        print("⚠ parent_student_links table already exists")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
