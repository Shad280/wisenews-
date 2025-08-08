#!/usr/bin/env python3
"""
MINIMAL ADMIN TEST - Railway
"""

from flask import Flask, jsonify, request, session, redirect, url_for, flash
import sqlite3
import bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

def init_simple_db():
    """Initialize simple database"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Create simple users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gdpr_consent BOOLEAN DEFAULT 1,
            marketing_consent BOOLEAN DEFAULT 0,
            analytics_consent BOOLEAN DEFAULT 1,
            data_processing_consent BOOLEAN DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
    # Delete existing admin
    cursor.execute('DELETE FROM users WHERE email = ?', ('admin@wisenews.com',))
    
    # Create admin user
    password_hash = bcrypt.hashpw('WiseNews2025!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin@wisenews.com', password_hash, 'Admin', 'User', 1))
    
    conn.commit()
    conn.close()
    print("✅ Simple admin user created")

def simple_auth(email, password):
    """Simple authentication"""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, password_hash, is_admin FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return True, user[0], user[2]  # success, user_id, is_admin
    return False, None, None

@app.route('/')
def index():
    return '''
    <h1>🎉 WiseNews Admin Test</h1>
    <p>Simple admin login test for Railway</p>
    <a href="/login">Test Login</a>
    <br><br>
    <b>Admin Credentials:</b><br>
    Email: admin@wisenews.com<br>
    Password: WiseNews2025!
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, user_id, is_admin = simple_auth(email, password)
        if success:
            session['user_id'] = user_id
            session['email'] = email
            session['is_admin'] = is_admin
            return f'''
            <h1>✅ LOGIN SUCCESS!</h1>
            <p>Email: {email}</p>
            <p>Admin: {'Yes' if is_admin else 'No'}</p>
            <a href="/admin">Go to Admin</a>
            '''
        else:
            return '''
            <h1>❌ LOGIN FAILED</h1>
            <p>Invalid credentials</p>
            <a href="/login">Try Again</a>
            '''
    
    return '''
    <h1>Login Test</h1>
    <form method="POST">
        Email: <input type="email" name="email" value="admin@wisenews.com" required><br><br>
        Password: <input type="password" name="password" value="WiseNews2025!" required><br><br>
        <button type="submit">Login</button>
    </form>
    '''

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return 'Admin access required'
    
    return f'''
    <h1>🎯 ADMIN DASHBOARD</h1>
    <p>Welcome {session.get('email')}</p>
    <p>You have admin access!</p>
    <a href="/logout">Logout</a>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🧪 Starting minimal admin test...")
    init_simple_db()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
