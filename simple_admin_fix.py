#!/usr/bin/env python3
"""Simple admin login test"""

import sqlite3
import bcrypt

def simple_admin_test():
    print("🧪 Creating simple admin user...")
    
    # Connect to database
    conn = sqlite3.connect('wisenews.db')
    cursor = conn.cursor()
    
    # Add is_admin column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE')
        print("✅ Added is_admin column")
    except:
        print("ℹ️  is_admin column already exists")
    
    # Delete existing admin if exists
    cursor.execute('DELETE FROM users WHERE email = ?', ('admin@wisenews.com',))
    print(f"✅ Removed existing admin users: {cursor.rowcount}")
    
    # Create simple admin user
    password_hash = bcrypt.hashpw('WiseNews2025!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute('''
        INSERT INTO users (
            email, password_hash, first_name, last_name,
            gdpr_consent, marketing_consent, analytics_consent, data_processing_consent,
            is_active, is_verified, is_admin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'admin@wisenews.com', password_hash, 'Admin', 'User',
        True, False, True, True,
        True, True, True
    ))
    
    print(f"✅ Created admin user: {cursor.lastrowid}")
    
    # Verify the admin user
    cursor.execute('SELECT id, email, is_admin, password_hash FROM users WHERE email = ?', ('admin@wisenews.com',))
    admin = cursor.fetchone()
    print(f"✅ Admin user verified: {admin}")
    
    # Test password
    password_valid = bcrypt.checkpw('WiseNews2025!'.encode('utf-8'), admin[3].encode('utf-8'))
    print(f"✅ Password valid: {password_valid}")
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    simple_admin_test()
