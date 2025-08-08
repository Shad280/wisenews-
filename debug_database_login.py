#!/usr/bin/env python3
"""
Database Login Debug Tool
Check what's actually in the database for login troubleshooting
"""

import sqlite3
import bcrypt
import os

def debug_database():
    """Debug database contents for login issues"""
    try:
        # Check if database exists
        db_path = 'wisenews.db'
        if not os.path.exists(db_path):
            print("❌ Database file doesn't exist!")
            return
        
        print(f"✅ Database file exists: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table structure
        print("\n📊 Users table structure:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Check if admin user exists
        print("\n🔍 Checking for admin user:")
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", ('admin@wisenews.com',))
        admin_count = cursor.fetchone()[0]
        print(f"  Admin users found: {admin_count}")
        
        if admin_count > 0:
            cursor.execute("SELECT id, email, password_hash, is_admin, is_active FROM users WHERE email = ?", ('admin@wisenews.com',))
            admin_data = cursor.fetchone()
            print(f"  ID: {admin_data[0]}")
            print(f"  Email: {admin_data[1]}")
            print(f"  Password hash length: {len(admin_data[2]) if admin_data[2] else 0}")
            print(f"  Is Admin: {admin_data[3]}")
            print(f"  Is Active: {admin_data[4]}")
            
            # Test password verification
            test_password = 'WiseNews2025!'
            stored_hash = admin_data[2]
            
            print(f"\n🔐 Testing password verification:")
            print(f"  Test password: {test_password}")
            print(f"  Stored hash: {stored_hash[:50]}...")
            
            try:
                # Test bcrypt verification
                is_valid = bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8'))
                print(f"  ✅ Password verification: {'PASS' if is_valid else 'FAIL'}")
                
                if not is_valid:
                    print("  🔧 Attempting to fix password...")
                    # Create new correct hash
                    new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, 'admin@wisenews.com'))
                    conn.commit()
                    print("  ✅ Password hash updated!")
                    
                    # Re-test
                    is_valid_new = bcrypt.checkpw(test_password.encode('utf-8'), new_hash.encode('utf-8'))
                    print(f"  ✅ New verification: {'PASS' if is_valid_new else 'FAIL'}")
                    
            except Exception as e:
                print(f"  ❌ Password verification error: {e}")
        
        # List all users
        print("\n👥 All users in database:")
        cursor.execute("SELECT id, email, is_admin, is_active FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  - ID: {user[0]}, Email: {user[1]}, Admin: {user[2]}, Active: {user[3]}")
        
        conn.close()
        print("\n✅ Database debug complete!")
        
    except Exception as e:
        print(f"❌ Database debug failed: {e}")

if __name__ == '__main__':
    debug_database()
