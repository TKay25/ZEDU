#!/usr/bin/env python3
"""
Script to create/initialize programmer/developer accounts
Run this to set up a developer account that can approve institutional admin applications
"""

import sys
from db_helper import create_tables, get_db_connection, create_programmer, get_all_programmers

def main():
    print("=" * 70)
    print("ZEDU Programmer Account Initialization")
    print("=" * 70)
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
    print("📊 Ensuring database schema is up to date...")
    
    if create_tables():
        print("✅ Database schema verified!")
    else:
        print("⚠️  Warning: Could not verify all tables, but continuing...")

    print()
    print("-" * 70)
    print("CREATE NEW PROGRAMMER ACCOUNT")
    print("-" * 70)
    print()

    email = input("Enter programmer email: ").strip()
    if not email:
        print("❌ Email is required")
        sys.exit(1)

    password = input("Enter programmer password: ").strip()
    if not password:
        print("❌ Password is required")
        sys.exit(1)

    full_name = input("Enter programmer full name: ").strip()
    if not full_name:
        print("❌ Full name is required")
        sys.exit(1)

    print()
    print("Select role:")
    print("1. developer (can review and approve admin applications)")
    print("2. system_admin (full system access)")
    print("3. super_admin (super admin access)")
    role_choice = input("Enter choice (1-3, default=1): ").strip() or "1"
    
    role_map = {"1": "developer", "2": "system_admin", "3": "super_admin"}
    role = role_map.get(role_choice, "developer")

    print()
    print("Creating programmer account...")
    print(f"  Email: {email}")
    print(f"  Name: {full_name}")
    print(f"  Role: {role}")
    print()

    result = create_programmer(email, password, full_name, role)
    
    if result['success']:
        print("✅ " + result['message'])
        print()
        print("=" * 70)
        print("PROGRAMMER ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Login Details:")
        print(f"  Portal: http://localhost:5000")
        print(f"  Click: Developer button (in navbar)")
        print(f"  Email: {email}")
        print(f"  Password: (the password you entered)")
        print()
        print("You can now:")
        print("  ✓ Review pending institutional admin applications")
        print("  ✓ Approve applications (which creates the admin account)")
        print("  ✓ Reject applications with reasons")
        print()
    else:
        print("❌ Error: " + result['message'])
        sys.exit(1)

    print()
    print("📋 Existing Programmers:")
    print("-" * 70)
    programmers = get_all_programmers(limit=100)
    if programmers:
        for prog in programmers:
            print(f"  • {prog['full_name']} ({prog['email']}) - {prog['role']}")
    else:
        print("  No programmers found")
    print("-" * 70)
    print()

if __name__ == "__main__":
    main()
