#!/usr/bin/env python3
"""
Ultra Simple Railway Login Test - Minimal Dependencies
"""

from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'

# Simple password check (no bcrypt to avoid dependency issues)
ADMIN_EMAIL = 'admin@wisenews.com'
ADMIN_PASSWORD = 'WiseNews2025!'

def init_simple_db():
    """Initialize simple database"""
    try:
        conn = sqlite3.connect('simple_auth.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simple_users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password TEXT,
                is_admin INTEGER DEFAULT 1
            )
        ''')
        
        # Delete and recreate admin
        cursor.execute('DELETE FROM simple_users WHERE email = ?', (ADMIN_EMAIL,))
        cursor.execute('INSERT INTO simple_users (email, password, is_admin) VALUES (?, ?, ?)', 
                      (ADMIN_EMAIL, ADMIN_PASSWORD, 1))
        
        conn.commit()
        conn.close()
        
        print("✅ Simple database initialized")
        return True
    except Exception as e:
        print(f"❌ Simple database init failed: {e}")
        return False

@app.route('/')
def index():
    """Homepage"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Railway Login Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        {% if session.user_email %}
            <div class="alert alert-success">
                <h1>🎉 SIMPLE LOGIN SUCCESS!</h1>
                <p><strong>Email:</strong> {{ session.user_email }}</p>
                <p><strong>Admin:</strong> {{ session.is_admin }}</p>
                <p><strong>Login Time:</strong> {{ session.login_time }}</p>
            </div>
            <a href="/logout" class="btn btn-secondary">Logout</a>
        {% else %}
            <div class="card">
                <div class="card-body text-center">
                    <h1>🔍 Simple Railway Login Test</h1>
                    <p>No bcrypt, no complex dependencies - just basic password check</p>
                    
                    <div class="alert alert-info">
                        <strong>Test Credentials:</strong><br>
                        Email: admin@wisenews.com<br>
                        Password: WiseNews2025!
                    </div>
                    
                    <a href="/login" class="btn btn-primary">Test Simple Login</a>
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
    """Simple login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        print(f"🔐 SIMPLE LOGIN ATTEMPT: {email}")
        
        # Simple validation
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            print("✅ Simple login success")
            session['user_email'] = ADMIN_EMAIL
            session['is_admin'] = True
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            flash('Simple login successful!', 'success')
            return redirect(url_for('index'))
        else:
            print(f"❌ Simple login failed: email='{email}', password='{password}'")
            flash(f'Simple login failed. Email: {email}, Password: {password}', 'error')
            return redirect(url_for('login'))
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Simple Login Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center">🔍 Simple Login Test</h2>
                        
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <div class="alert alert-warning">
                            <strong>Simple Test:</strong> No bcrypt, just plain text comparison<br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" 
                                       value="admin@wisenews.com" placeholder="Email" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" name="password" class="form-control" 
                                       value="WiseNews2025!" placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Simple Login Test</button>
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
    flash('Logged out', 'success')
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """Status check"""
    return {
        'status': 'success',
        'message': 'Simple Railway Login Test Active',
        'version': 'simple-v1',
        'admin_credentials': f'{ADMIN_EMAIL} / {ADMIN_PASSWORD}'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🔍 Simple Railway Login Test Starting...")
    print(f"✅ Running on {host}:{port}")
    print(f"🔑 Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    
    init_simple_db()
    
    app.run(host=host, port=port, debug=False)
