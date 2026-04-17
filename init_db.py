#!/usr/bin/env python3
"""
Database initialization script for ZEDU
Run this script once to initialize the database and create all necessary tables
"""

import sys
from db_helper import create_tables, get_db_connection

def main():
    print("=" * 60)
    print("ZEDU Database Initialization Script")
    print("=" * 60)
    print()

    # Test connection
    print("🔌 Testing database connection...")
    conn = get_db_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
    else:
        print("❌ Failed to connect to database")
        print("Please check your database connection string")
        sys.exit(1)

    print()
    print("📊 Creating database tables...")
    
    if create_tables():
        print()
        print("✅ Database initialization complete!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the Flask app: python app.py")
        print("3. Open http://localhost:5000 in your browser")
        print()
        print("=" * 60)
    else:
        print("❌ Failed to create tables")
        sys.exit(1)

if __name__ == "__main__":
    main()
