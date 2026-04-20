#!/usr/bin/env python3
"""
Migration script to add administrator applications table to ZEDU database
Run this once to set up the administrator approval system
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://zeduweb_user:qdEe6bfJmlIHAknO2TVbum3SSm2kFvFV@dpg-d7cklfa8qa3s73e9podg-a.oregon-postgres.render.com/zeduweb"

def run_migration():
    """Run the migration to add admin_applications table"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create admin_applications table for pending applications
        print("Creating admin_applications table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_applications (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                org_name VARCHAR(255) NOT NULL,
                org_type VARCHAR(100) NOT NULL CHECK (org_type IN ('primary_school', 'secondary_school', 'university', 'training_center', 'tutoring_center', 'corporate', 'other')),
                org_phone VARCHAR(20) NOT NULL,
                org_address TEXT NOT NULL,
                org_city VARCHAR(100) NOT NULL,
                org_state VARCHAR(100) NOT NULL,
                org_zip VARCHAR(20) NOT NULL,
                payment_plan VARCHAR(50) NOT NULL CHECK (payment_plan IN ('students_pay', 'school_pays', 'hybrid')),
                estimated_student_count INTEGER NOT NULL,
                country_code VARCHAR(5),
                whatsapp_number VARCHAR(20),
                status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by_admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL
            );
        """)
        
        # Create approved_admins table for active administrators
        print("Creating approved_admins table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approved_admins (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                application_id INTEGER NOT NULL REFERENCES admin_applications(id) ON DELETE CASCADE,
                org_name VARCHAR(255) NOT NULL,
                org_type VARCHAR(100) NOT NULL,
                org_phone VARCHAR(20) NOT NULL,
                org_address TEXT NOT NULL,
                org_city VARCHAR(100) NOT NULL,
                org_state VARCHAR(100) NOT NULL,
                org_zip VARCHAR(20) NOT NULL,
                payment_plan VARCHAR(50) NOT NULL,
                estimated_student_count INTEGER NOT NULL,
                status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'terminated')),
                approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for better query performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_app_email ON admin_applications(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_app_status ON admin_applications(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_app_created ON admin_applications(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_approved_admin_user ON approved_admins(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_approved_admin_status ON approved_admins(status);")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.errors.DuplicateTable:
        print("⚠ admin_applications and/or approved_admins tables already exist")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
