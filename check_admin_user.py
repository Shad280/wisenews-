import sqlite3
import bcrypt

conn = sqlite3.connect('wisenews.db')
cursor = conn.cursor()

cursor.execute('SELECT id, email, password_hash FROM users WHERE email = ?', ('admin@wisenews.com',))
user = cursor.fetchone()

if user:
    print(f'Admin user found: ID={user[0]}, Email={user[1]}')
    print(f'Password hash exists: {bool(user[2])}')
    
    # Test password verification
    test_password = 'WiseNews2025!'
    if user[2]:
        try:
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), user[2].encode('utf-8'))
            print(f'Password verification: {is_valid}')
        except Exception as e:
            print(f'Password verification error: {e}')
else:
    print('No admin user found')

conn.close()
