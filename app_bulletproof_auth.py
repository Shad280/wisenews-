#!/usr/bin/env python3
"""
WiseNews - Bulletproof Authentication Fix
Direct database authentication without complex dependencies
"""

from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_bulletproof_auth():
    """Initialize bulletproof authentication"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT DEFAULT 'Admin',
                last_name TEXT DEFAULT 'User',
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                last_ip_address TEXT
            )
        ''')
        
        # Delete any existing admin to start fresh
        cursor.execute('DELETE FROM users WHERE email = ?', ('admin@wisenews.com',))
        
        # Create admin with bulletproof password
        admin_password = 'WiseNews2025!'
        password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, is_admin, is_active, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin@wisenews.com', password_hash, 'Admin', 'User', 1, 1, 1))
        
        admin_id = cursor.lastrowid
        conn.commit()
        
        # Verify admin creation
        cursor.execute('SELECT id, email, is_admin FROM users WHERE email = ?', ('admin@wisenews.com',))
        admin_check = cursor.fetchone()
        
        # Test password immediately
        test_result = bcrypt.checkpw(admin_password.encode('utf-8'), password_hash.encode('utf-8'))
        
        conn.close()
        
        print(f"✅ Bulletproof Auth Setup Complete!")
        print(f"   Admin ID: {admin_id}")
        print(f"   Email: admin@wisenews.com")
        print(f"   Password Test: {'PASS' if test_result else 'FAIL'}")
        print(f"   Verification: {'SUCCESS' if admin_check else 'FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bulletproof auth setup failed: {e}")
        return False

@app.route('/')
def index():
    """Homepage with login status"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiseNews - Bulletproof Authentication</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-newspaper me-2"></i>WiseNews - Bulletproof Auth
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.user_id %}
                    <span class="navbar-text me-3">
                        <i class="fas fa-user"></i> {{ session.user_email }}
                        {% if session.is_admin %}<span class="badge bg-warning ms-1">Admin</span>{% endif %}
                    </span>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                {% else %}
                    <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        {% if session.user_id %}
            <div class="alert alert-success">
                <h2><i class="fas fa-check-circle"></i> 🎉 LOGIN SUCCESS!</h2>
                <p><strong>Authentication Fixed!</strong></p>
                <hr>
                <p><strong>User Details:</strong></p>
                <ul>
                    <li><strong>ID:</strong> {{ session.user_id }}</li>
                    <li><strong>Email:</strong> {{ session.user_email }}</li>
                    <li><strong>Admin:</strong> {{ 'Yes' if session.is_admin else 'No' }}</li>
                    <li><strong>Login Time:</strong> {{ session.login_time }}</li>
                </ul>
                
                {% if session.is_admin %}
                    <div class="mt-3">
                        <a href="/admin" class="btn btn-warning">
                            <i class="fas fa-cog"></i> Admin Dashboard
                        </a>
                    </div>
                {% endif %}
            </div>
        {% else %}
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body text-center">
                            <h1><i class="fas fa-shield-alt"></i> WiseNews Bulletproof Authentication</h1>
                            <p class="lead">Comprehensive login fix deployed!</p>
                            
                            <div class="alert alert-info">
                                <h5><i class="fas fa-key"></i> Test Credentials</h5>
                                <p><strong>Email:</strong> admin@wisenews.com<br>
                                <strong>Password:</strong> WiseNews2025!</p>
                            </div>
                            
                            <a href="/login" class="btn btn-primary btn-lg">
                                <i class="fas fa-sign-in-alt"></i> Test Login Now
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        {% endif %}
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="mt-3">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Bulletproof login system"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            ip_address = request.remote_addr or '127.0.0.1'
            
            print(f"🔐 BULLETPROOF LOGIN ATTEMPT:")
            print(f"   Email: '{email}'")
            print(f"   Password Length: {len(password)}")
            print(f"   IP: {ip_address}")
            
            # Validate input
            if not email or not password:
                print("❌ Missing email or password")
                flash('Email and password are required', 'error')
                return redirect(url_for('login'))
            
            # Connect to database
            conn = get_db()
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('SELECT id, email, password_hash, is_admin, is_active FROM users WHERE LOWER(email) = ?', (email,))
            user = cursor.fetchone()
            
            if not user:
                print(f"❌ User not found: {email}")
                
                # Special case: create admin if trying to login as admin
                if email == 'admin@wisenews.com':
                    print("🔧 Creating missing admin user...")
                    try:
                        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute('''
                            INSERT INTO users (email, password_hash, first_name, last_name, is_admin, is_active, is_verified)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (email, password_hash, 'Admin', 'User', 1, 1, 1))
                        
                        user_id = cursor.lastrowid
                        conn.commit()
                        
                        print(f"✅ Created admin user with ID: {user_id}")
                        
                        # Set session and redirect
                        session['user_id'] = user_id
                        session['user_email'] = email
                        session['is_admin'] = True
                        session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        conn.close()
                        flash('Admin account created and logged in successfully!', 'success')
                        return redirect(url_for('index'))
                        
                    except Exception as create_error:
                        print(f"❌ Failed to create admin: {create_error}")
                        conn.close()
                        flash(f'Failed to create admin: {create_error}', 'error')
                        return redirect(url_for('login'))
                else:
                    conn.close()
                    flash('Invalid email address', 'error')
                    return redirect(url_for('login'))
            
            # User found - verify password
            user_id, user_email, stored_hash, is_admin, is_active = user
            print(f"✅ User found: ID={user_id}, Email={user_email}")
            
            if not is_active:
                print("❌ Account inactive")
                conn.close()
                flash('Account is inactive', 'error')
                return redirect(url_for('login'))
            
            # Password verification with extensive debugging
            print(f"🔐 Password verification:")
            print(f"   Stored hash length: {len(stored_hash) if stored_hash else 0}")
            print(f"   Password: '{password}'")
            
            try:
                password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                print(f"   Bcrypt result: {password_valid}")
                
                if password_valid:
                    # Update last login
                    cursor.execute('UPDATE users SET last_login = ?, last_ip_address = ? WHERE id = ?', 
                                 (datetime.now().isoformat(), ip_address, user_id))
                    conn.commit()
                    conn.close()
                    
                    # Set session
                    session['user_id'] = user_id
                    session['user_email'] = user_email
                    session['is_admin'] = bool(is_admin)
                    session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"🎉 LOGIN SUCCESS for {user_email}")
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    print("❌ Password verification failed")
                    conn.close()
                    flash('Invalid credentials - password incorrect', 'error')
                    return redirect(url_for('login'))
                    
            except Exception as bcrypt_error:
                print(f"❌ Bcrypt error: {bcrypt_error}")
                conn.close()
                flash(f'Password verification error: {bcrypt_error}', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"❌ Login system error: {e}")
            flash(f'Login system error: {e}', 'error')
            return redirect(url_for('login'))
    
    # GET request - show login form
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - WiseNews Bulletproof Auth</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center mb-4">
                            <i class="fas fa-shield-alt"></i> WiseNews Login
                        </h2>
                        
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">
                                        <i class="fas fa-{{ 'exclamation-triangle' if category == 'error' else 'check-circle' }}"></i>
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <div class="alert alert-info">
                            <h5><i class="fas fa-key"></i> Bulletproof Authentication Test</h5>
                            <p><strong>Email:</strong> admin@wisenews.com<br>
                            <strong>Password:</strong> WiseNews2025!</p>
                            <small>This system will auto-create the admin account if it doesn't exist.</small>
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email Address</label>
                                <input type="email" name="email" id="email" class="form-control" 
                                       value="admin@wisenews.com" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" name="password" id="password" class="form-control" 
                                       value="WiseNews2025!" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 btn-lg">
                                <i class="fas fa-sign-in-alt"></i> Login
                            </button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <a href="/">← Back to Homepage</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/admin')
def admin():
    """Admin dashboard"""
    if not session.get('user_id'):
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    if not session.get('is_admin'):
        flash('Admin access required', 'error')
        return redirect(url_for('index'))
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-success">
            <h1><i class="fas fa-crown"></i> Admin Dashboard</h1>
            <p><strong>✅ Admin login successful!</strong></p>
            <p>Email: {{ session.user_email }}</p>
            <p>User ID: {{ session.user_id }}</p>
            <p>Login Time: {{ session.login_time }}</p>
        </div>
        <div class="text-center">
            <a href="/" class="btn btn-primary">← Back to Home</a>
            <a href="/logout" class="btn btn-secondary">Logout</a>
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

@app.route('/api/status')
def api_status():
    """API status"""
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Bulletproof Authentication Active',
        'timestamp': datetime.now().isoformat(),
        'version': 'bulletproof-auth-v1',
        'features': ['Direct SQLite Auth', 'Auto Admin Creation', 'Bcrypt Password Hashing', 'Session Management']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🛡️  WiseNews Bulletproof Authentication Starting...")
    print(f"🚀 Running on {host}:{port}")
    print("🔧 Initializing bulletproof authentication...")
    
    if init_bulletproof_auth():
        print("✅ Bulletproof authentication ready!")
        print("🔑 Login with: admin@wisenews.com / WiseNews2025!")
    else:
        print("❌ Authentication setup failed!")
    
    app.run(host=host, port=port, debug=False)
