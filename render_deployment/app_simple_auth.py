#!/usr/bin/env python3
"""
WiseNews Simple Auth Version for Render
Working authentication without complex dependencies
"""

from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_simple_auth():
    """Initialize simple authentication"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin user with simple hash
        admin_email = 'admin@wisenews.com'
        admin_password = 'WiseNews2025!'
        password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (email, password_hash, is_admin)
            VALUES (?, ?, 1)
        ''', (admin_email, password_hash))
        
        conn.commit()
        conn.close()
        print("✅ Simple authentication initialized")
        
    except Exception as e:
        print(f"❌ Auth initialization failed: {e}")

def verify_password(password, password_hash):
    """Simple password verification"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

@app.route('/')
def index():
    """Homepage"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiseNews - Smart News Aggregation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-newspaper me-2"></i>WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.user_id %}
                    <span class="nav-link">Welcome, {{ session.user_email }}!</span>
                    <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                {% else %}
                    <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="hero-section bg-primary text-white text-center py-5">
        <div class="container">
            <h1 class="display-4 fw-bold mb-3">
                🎉 WiseNews Authentication is Working!
            </h1>
            <p class="lead mb-4">
                Render Deployment with Simple Authentication System
            </p>
            <div class="alert alert-success d-inline-block">
                <i class="fas fa-check-circle"></i> <strong>SUCCESS!</strong> 
                Login functionality is now operational!
            </div>
        </div>
    </div>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Test Authentication</h5>
                        <p class="card-text">Click below to test the login system</p>
                        <div class="alert alert-info">
                            <strong>Login Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        <a href="/login" class="btn btn-primary btn-lg">
                            <i class="fas fa-sign-in-alt"></i> Test Login Now
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login with simple authentication"""
    error_message = None
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            if user and verify_password(password, user['password_hash']):
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('dashboard'))
            else:
                error_message = 'Invalid email or password'
                
        except Exception as e:
            error_message = f'Login error: {e}'
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Login - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center">WiseNews Login</h2>
                        
                        {% if error_message %}
                            <div class="alert alert-danger">{{ error_message }}</div>
                        {% endif %}
                        
                        <div class="alert alert-info">
                            <strong>Test Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" name="email" id="email" class="form-control" 
                                       value="admin@wisenews.com" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" name="password" id="password" class="form-control" 
                                       placeholder="Enter password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
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
    ''', error_message=error_message)

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-success">
            <h1>🎉 Login Successful!</h1>
            <p><strong>Welcome to WiseNews Dashboard!</strong></p>
            <p><strong>Email:</strong> {{ session.user_email }}</p>
            <p><strong>Admin:</strong> {{ 'Yes' if session.is_admin else 'No' }}</p>
            <p><strong>User ID:</strong> {{ session.user_id }}</p>
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
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """API status"""
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Simple Auth Working!',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0-simple-auth',
        'authentication': 'ENABLED',
        'login_test': 'admin@wisenews.com / WiseNews2025!'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🗞️  WiseNews Simple Auth starting...")
    print("🔐 Initializing authentication...")
    init_simple_auth()
    print("✅ WiseNews Simple Auth ready!")
    print("🔑 Test login: admin@wisenews.com / WiseNews2025!")
    
    app.run(host=host, port=port, debug=False)
