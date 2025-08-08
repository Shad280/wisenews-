#!/usr/bin/env python3
"""
Reset password for stamound1@outlook.com account
"""
import sqlite3
import bcrypt

def reset_user_password():
    """Reset password for the stamound1 account"""
    print("=== Resetting Password for stamound1@outlook.com ===")
    
    email = 'stamound1@outlook.com'
    new_password = 'admin123'
    
    # Hash the new password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, email FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {email} not found")
            return False
        
        print(f"Found user: ID {user[0]}, Email: {user[1]}")
        
        # Update password
        cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (password_hash, email))
        conn.commit()
        
        print(f"✅ Password reset successfully for {email}")
        print(f"New password: {new_password}")
        
        # Verify the update
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        updated_hash = cursor.fetchone()[0]
        
        # Test the new password
        test_verify = bcrypt.checkpw(new_password.encode('utf-8'), updated_hash.encode('utf-8'))
        print(f"Password verification test: {test_verify}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

if __name__ == "__main__":
    reset_user_password()
