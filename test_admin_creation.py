#!/usr/bin/env python3
"""Test admin user creation"""

import sqlite3
import bcrypt
import user_auth

def test_admin_creation():
    print("🧪 Testing admin user creation...")
    
    # Create user manager
    user_manager = user_auth.UserManager('wisenews.db')
    
    # Try to create admin user
    result = user_manager.create_admin_user(
        email='admin@wisenews.com',
        password='WiseNews2025!'
    )
    
    print(f"✅ Admin creation result: {result}")
    
    # Check if admin exists in database
    conn = sqlite3.connect('wisenews.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, email, is_admin, password_hash FROM users WHERE email = ?', ('admin@wisenews.com',))
    admin_user = cursor.fetchone()
    
    if admin_user:
        user_id, email, is_admin, password_hash = admin_user
        print(f"✅ Admin user found:")
        print(f"   - ID: {user_id}")
        print(f"   - Email: {email}")
        print(f"   - Is Admin: {is_admin}")
        print(f"   - Password Hash: {password_hash[:20]}...")
        
        # Test password verification
        password_valid = bcrypt.checkpw('WiseNews2025!'.encode('utf-8'), password_hash.encode('utf-8'))
        print(f"   - Password Valid: {password_valid}")
        
        # Test authentication
        success, message, user_id_auth = user_manager.authenticate_user(
            'admin@wisenews.com', 
            'WiseNews2025!', 
            '127.0.0.1'
        )
        print(f"   - Authentication: {success} - {message}")
        
    else:
        print("❌ Admin user not found in database")
    
    conn.close()

if __name__ == '__main__':
    test_admin_creation()
