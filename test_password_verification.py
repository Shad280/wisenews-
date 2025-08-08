#!/usr/bin/env python3
"""
Test password verification directly
"""
import sqlite3
import bcrypt

def test_password_verification():
    """Test password verification directly"""
    print("=== Direct Password Verification Test ===")
    
    # Get user from database
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT email, password_hash FROM users WHERE email = ?', ('stamound1@outlook.com',))
    result = cursor.fetchone()
    
    if not result:
        print("❌ User not found")
        return
    
    email, stored_hash = result
    print(f"User: {email}")
    print(f"Stored hash: {stored_hash}")
    
    # Test password verification
    test_password = 'admin123'
    print(f"Testing password: {test_password}")
    
    try:
        # Verify password
        is_valid = bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8'))
        print(f"Password verification result: {is_valid}")
        
        if is_valid:
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")
            
        # Also test what happens if we hash the test password
        test_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        print(f"New hash for same password: {test_hash.decode('utf-8')}")
        
        # Verify the new hash works
        verify_new = bcrypt.checkpw(test_password.encode('utf-8'), test_hash)
        print(f"New hash verification: {verify_new}")
        
    except Exception as e:
        print(f"❌ Password verification error: {e}")
    
    conn.close()

if __name__ == "__main__":
    test_password_verification()
