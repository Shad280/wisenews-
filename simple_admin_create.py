import sqlite3
import bcrypt
from datetime import datetime

def create_simple_admin():
    """Create admin user directly in database"""
    print("Creating admin user...")
    
    admin_email = "admin@wisenews.com"
    admin_password = "WiseNews2025!"
    
    # Hash password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = sqlite3.connect('wisenews.db')
    cursor = conn.cursor()
    
    # Delete existing admin if exists
    cursor.execute('DELETE FROM users WHERE email = ?', (admin_email,))
    
    # Create new admin
    cursor.execute('''
        INSERT INTO users (
            email, password_hash, first_name, last_name, 
            is_active, is_verified, gdpr_consent, data_processing_consent,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        admin_email, password_hash, 'WiseNews', 'Administrator',
        1, 1, 1, 1, datetime.now().isoformat()
    ))
    
    admin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Admin created with ID: {admin_id}")
    print(f"📧 Email: {admin_email}")
    print(f"🔑 Password: {admin_password}")
    
    return admin_id

if __name__ == "__main__":
    create_simple_admin()
