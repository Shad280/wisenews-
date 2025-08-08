#!/usr/bin/env python3
"""
Minimal WiseNews Login Test - Isolate Authentication Issues
"""

from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import os
import sqlite3
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_minimal_db():
    """Initialize minimal database for testing"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 1,
                gdpr_consent BOOLEAN DEFAULT 0,
                marketing_consent BOOLEAN DEFAULT 0,
                analytics_consent BOOLEAN DEFAULT 0,
                data_processing_consent BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Delete existing admin
        cursor.execute('DELETE FROM users WHERE email = ?', ('admin@wisenews.com',))
        
        # Create admin user
        password_hash = bcrypt.hashpw('WiseNews2025!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (
                email, password_hash, first_name, last_name,
                is_admin, is_active, is_verified,
                gdpr_consent, marketing_consent, analytics_consent, data_processing_consent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin@wisenews.com', password_hash, 'Admin', 'User',
            1, 1, 1, 1, 0, 1, 1
        ))
        
        conn.commit()
        admin_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Minimal admin user created with ID: {admin_id}")
        
        # Verify creation
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, is_admin FROM users WHERE email = ?', ('admin@wisenews.com',))
        admin_check = cursor.fetchone()
        conn.close()
        
        if admin_check:
            print(f"✅ Admin verification: ID={admin_check[0]}, Email={admin_check[1]}, Admin={admin_check[2]}")
            return True
        else:
            print("❌ Admin verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Minimal database initialization failed: {e}")
        return False

@app.route('/')
def index():
    """Homepage"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>WiseNews - Login Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="text-center">
            <h1>🔍 WiseNews Login Test</h1>
            <p>Minimal authentication testing</p>
            {% if session.user_id %}
                <div class="alert alert-success">
                    <h3>✅ LOGIN SUCCESS!</h3>
                    <p>User ID: {{ session.user_id }}</p>
                    <p>Email: {{ session.user_email }}</p>
                    <p>Admin: {{ session.is_admin }}</p>
                </div>
                <a href="/logout" class="btn btn-secondary">Logout</a>
            {% else %}
                <div class="alert alert-info">
                    <strong>Test Credentials:</strong><br>
                    Email: admin@wisenews.com<br>
                    Password: WiseNews2025!
                </div>
                <a href="/login" class="btn btn-primary">Test Login</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Minimal login test"""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            print(f"🔐 Login attempt: {email}")
            
            # Get user from database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, email, password_hash, is_admin FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                print(f"✅ User found: ID={user[0]}, Email={user[1]}")
                
                # Check password
                if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                    print("✅ Password correct")
                    
                    # Set session
                    session['user_id'] = user[0]
                    session['user_email'] = user[1]
                    session['is_admin'] = bool(user[3])
                    
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    print("❌ Password incorrect")
                    flash('Invalid password', 'error')
            else:
                print("❌ User not found")
                flash('User not found', 'error')
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            flash(f'Login error: {e}', 'error')
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Login Test - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center">🔍 Login Test</h2>
                        
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <div class="alert alert-info">
                            <strong>Test Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" placeholder="Email" value="admin@wisenews.com" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" name="password" class="form-control" placeholder="Password" value="WiseNews2025!" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Test Login</button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <a href="/">← Back to Home</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🔍 WiseNews Minimal Login Test Starting... v2")
    print(f"🚀 Running on {host}:{port}")
    print(f"⚡ Force Fresh Deploy: 2025-08-08 20:30")
    
    # Initialize minimal database
    if init_minimal_db():
        print("✅ Minimal database ready!")
    else:
        print("❌ Database setup failed!")
    
    print("🔑 Test with: admin@wisenews.com / WiseNews2025!")
    
    app.run(host=host, port=port, debug=True)
