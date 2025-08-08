import sqlite3

conn = sqlite3.connect('wisenews.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('Tables in wisenews.db:')
for table in tables:
    print(f'- {table[0]}')

# Check if users table exists
if any('users' in table for table in tables):
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'\nUsers table exists with {user_count} users')
    
    if user_count > 0:
        cursor.execute('SELECT id, email, first_name, last_name FROM users')
        users = cursor.fetchall()
        print('Existing users:')
        for user in users:
            print(f'  ID: {user[0]}, Email: {user[1]}, Name: {user[2]} {user[3]}')
else:
    print('\nUsers table does not exist')

conn.close()
