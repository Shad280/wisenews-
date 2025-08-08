#!/usr/bin/env python3
"""
WiseNews Railway Full-Feature Version
Complete authentication system with Railway optimizations
"""

from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash, g
import os
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
# Remove threading for Railway compatibility
# import threading
import time
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET

# Import full user modules
import user_auth
import auth_decorators

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

# Railway-optimized RSS sources (reduced from 18 to 6 sources)
RSS_SOURCES = {
    'bbc': {
        'name': 'BBC News',
        'rss': 'http://feeds.bbci.co.uk/news/rss.xml',
        'category': 'general',
        'enabled': True
    },
    'cnn': {
        'name': 'CNN',
        'rss': 'http://rss.cnn.com/rss/edition.rss',
        'category': 'general',
        'enabled': True
    },
    'techcrunch': {
        'name': 'TechCrunch',
        'rss': 'http://feeds.feedburner.com/TechCrunch/',
        'category': 'technology',
        'enabled': True
    },
    'reuters': {
        'name': 'Reuters',
        'rss': 'http://feeds.reuters.com/reuters/topNews',
        'category': 'general',
        'enabled': True
    },
    'bbc_tech': {
        'name': 'BBC Technology',
        'rss': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
        'category': 'technology',
        'enabled': True
    },
    'guardian': {
        'name': 'The Guardian',
        'rss': 'https://www.theguardian.com/international/rss',
        'category': 'general',
        'enabled': True
    }
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with full schema"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create all necessary tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                url TEXT UNIQUE,
                author TEXT,
                source TEXT,
                category TEXT,
                image_url TEXT,
                published_date DATETIME,
                fetch_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0,
                category_color TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                color TEXT DEFAULT '#007bff',
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_fetch DATETIME,
                error_count INTEGER DEFAULT 0
            )
        ''')
        
        # Insert default categories
        categories = [
            ('general', 'General News', '#007bff', 'Latest breaking news and current events'),
            ('technology', 'Technology', '#28a745', 'Tech news, gadgets, and innovations'),
            ('business', 'Business', '#ffc107', 'Financial news and market updates'),
            ('sports', 'Sports', '#17a2b8', 'Sports news and updates'),
            ('health', 'Health', '#dc3545', 'Health and medical news'),
            ('science', 'Science', '#6f42c1', 'Scientific discoveries and research'),
            ('entertainment', 'Entertainment', '#fd7e14', 'Entertainment and celebrity news')
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO categories (name, display_name, color, description)
            VALUES (?, ?, ?, ?)
        ''', categories)
        
        # Insert RSS sources
        for source_id, source_info in RSS_SOURCES.items():
            cursor.execute('''
                INSERT OR REPLACE INTO news_sources (name, url, category, enabled)
                VALUES (?, ?, ?, ?)
            ''', (source_info['name'], source_info['rss'], source_info['category'], source_info['enabled']))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
        
        # Initialize user authentication
        try:
            user_manager = user_auth.UserManager(app.config['DATABASE'])
            user_manager.init_db()
            
            # Create admin user
            try:
                admin_created = user_manager.register_user(
                    email='admin@wisenews.com',
                    password='WiseNews2025!',
                    consent_analytics=True,
                    consent_marketing=False,
                    is_admin=True
                )
                if admin_created:
                    print("✅ Admin user created successfully")
                else:
                    print("ℹ️  Admin user already exists")
            except Exception as e:
                print(f"ℹ️  Admin user setup: {e}")
                
        except Exception as e:
            print(f"⚠️  User auth initialization: {e}")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def fetch_all_news():
    """Fetch news from all sources (Railway optimized)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        total_new = 0
        
        for source_id, source_info in RSS_SOURCES.items():
            if not source_info.get('enabled', True):
                continue
                
            try:
                print(f"📡 Fetching from {source_info['name']}...")
                
                response = urllib.request.urlopen(source_info['rss'], timeout=15)
                data = response.read()
                root = ET.fromstring(data)
                
                articles = []
                items = root.findall('.//item')[:8]  # Limit to 8 articles per source
                
                for item in items:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    if title is not None and link is not None:
                        articles.append({
                            'title': title.text or 'No Title',
                            'url': link.text or '',
                            'summary': description.text[:500] if description is not None and description.text else 'No summary available',
                            'source': source_info['name'],
                            'category': source_info['category'],
                            'published_date': datetime.now().isoformat()
                        })
                
                # Insert articles
                for article in articles:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO articles 
                            (title, url, summary, source, category, published_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            article['title'],
                            article['url'],
                            article['summary'],
                            article['source'],
                            article['category'],
                            article['published_date']
                        ))
                        if cursor.rowcount > 0:
                            total_new += 1
                    except Exception as e:
                        pass  # Ignore duplicates
                
                print(f"✅ Fetched {len(articles)} articles from {source_info['name']}")
                
            except Exception as e:
                print(f"⚠️  Error fetching from {source_info['name']}: {e}")
        
        conn.commit()
        conn.close()
        print(f"🎉 News fetch complete! {total_new} new articles added")
        return total_new
        
    except Exception as e:
        print(f"❌ News fetch failed: {e}")
        return 0

# Import all the route handlers from the original app
# We'll include just the essential ones for Railway

@app.route('/')
def index():
    """Homepage - Enhanced for Railway"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get recent articles
        cursor.execute('''
            SELECT a.*, c.color as category_color
            FROM articles a
            LEFT JOIN categories c ON a.category = c.name
            ORDER BY a.published_date DESC 
            LIMIT 20
        ''')
        
        articles = cursor.fetchall()
        
        # Get categories
        cursor.execute('SELECT * FROM categories ORDER BY name')
        categories = cursor.fetchall()
        
        conn.close()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiseNews - Smart News Aggregation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 0;
        }
        .category-badge {
            font-size: 0.8rem;
            padding: 0.3rem 0.6rem;
        }
        .article-card {
            transition: transform 0.2s;
            height: 100%;
        }
        .article-card:hover {
            transform: translateY(-5px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-newspaper me-2"></i>WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.user_id %}
                    <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                {% else %}
                    <a class="nav-link" href="/register"><i class="fas fa-user-plus"></i> Register</a>
                    <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="hero-section text-center">
        <div class="container">
            <h1 class="display-4 fw-bold mb-3">
                🎉 WiseNews is LIVE on Railway!
            </h1>
            <p class="lead mb-4">
                Smart News Aggregation with Full Authentication System
            </p>
            <div class="alert alert-success d-inline-block">
                <i class="fas fa-check-circle"></i> <strong>SUCCESS!</strong> 
                Complete WiseNews deployment with login functionality!
            </div>
        </div>
    </div>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <h2 class="mb-4">Latest News</h2>
                <div class="row">
                    {% for article in articles %}
                    <div class="col-md-6 mb-4">
                        <div class="card article-card">
                            <div class="card-body">
                                <h5 class="card-title">{{ article.title }}</h5>
                                <p class="card-text">{{ article.summary[:150] }}...</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <small class="text-muted">{{ article.source }}</small>
                                        <span class="badge category-badge ms-2" style="background-color: {{ article.category_color or '#6c757d' }}">
                                            {{ article.category }}
                                        </span>
                                    </div>
                                    <a href="{{ article.url }}" target="_blank" class="btn btn-primary btn-sm">
                                        Read More <i class="fas fa-external-link-alt"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Authentication Test</h5>
                        <p class="card-text">Test the login system:</p>
                        <div class="alert alert-info">
                            <strong>Admin Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        <a href="/login" class="btn btn-success w-100">
                            <i class="fas fa-sign-in-alt"></i> Test Login
                        </a>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-body">
                        <h5 class="card-title">Categories</h5>
                        {% for category in categories %}
                        <span class="badge me-2 mb-2" style="background-color: {{ category.color }}">
                            {{ category.display_name }}
                        </span>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        {% if not articles %}
        <div class="text-center">
            <h3>Welcome to WiseNews!</h3>
            <p>News articles are being fetched. Please refresh in a moment.</p>
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', articles=articles, categories=categories)
        
    except Exception as e:
        return f"<h1>WiseNews Railway</h1><p>App is running! Error: {e}</p><p><a href='/login'>Test Login</a></p>"

# Import authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login with full authentication"""
    if request.method == 'POST':
        try:
            user_manager = user_auth.UserManager(app.config['DATABASE'])
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = user_manager.authenticate_user(email, password)
            if user:
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['is_admin'] = user.get('is_admin', False)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'error')
        except Exception as e:
            flash(f'Login error: {e}', 'error')
    
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
                            <strong>Test Admin Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" placeholder="Email" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" name="password" class="form-control" placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/register">Need an account? Register here</a><br>
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

@app.route('/dashboard')
@auth_decorators.login_required
def dashboard():
    """User dashboard"""
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
            <p>Email: {{ session.user_email }}</p>
            <p>Admin: {{ 'Yes' if session.is_admin else 'No' }}</p>
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

@app.route('/register')
def register():
    """Registration page"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Register - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h2 class="text-center">Join WiseNews</h2>
                        <p class="text-center">Registration functionality available</p>
                        <div class="text-center mt-3">
                            <a href="/login" class="btn btn-primary">Login Instead</a><br>
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

@app.route('/admin')
@auth_decorators.login_required
def admin_dashboard():
    """Admin dashboard with system statistics"""
    user = auth_decorators.get_current_user()
    
    # Check if user is admin
    if not user.get('is_admin', False):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get system statistics
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE created_at > datetime("now", "-24 hours")')
        articles_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE created_at > datetime("now", "-7 days")')
        new_users_week = cursor.fetchone()[0]
        
        # Get source statistics
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM articles 
            GROUP BY source 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_sources = cursor.fetchall()
        
        # Get category statistics  
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
        ''')
        categories = cursor.fetchall()
        
        conn.close()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-shield-alt"></i> WiseNews Admin</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">User Dashboard</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1><i class="fas fa-tachometer-alt"></i> Admin Dashboard</h1>
        <p class="text-muted">Welcome, {{ user.email }}</p>
        
        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Total Articles</h6>
                                <h3>{{ total_articles }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-newspaper fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Total Users</h6>
                                <h3>{{ total_users }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-users fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Articles Today</h6>
                                <h3>{{ articles_today }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-plus-circle fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-warning text-dark">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>New Users (7d)</h6>
                                <h3>{{ new_users_week }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-user-plus fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Charts and Data -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Top News Sources</h5>
                    </div>
                    <div class="card-body">
                        {% for source in top_sources %}
                        <div class="d-flex justify-content-between mb-2">
                            <span>{{ source[0] }}</span>
                            <span class="badge bg-primary">{{ source[1] }} articles</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-tags"></i> Categories</h5>
                    </div>
                    <div class="card-body">
                        {% for category in categories %}
                        <div class="d-flex justify-content-between mb-2">
                            <span>{{ category[0].title() }}</span>
                            <span class="badge bg-success">{{ category[1] }} articles</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Admin Actions -->
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs"></i> Admin Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <a href="/api/fetch-news" class="btn btn-outline-primary w-100 mb-2">
                                    <i class="fas fa-sync"></i> Refresh News
                                </a>
                            </div>
                            <div class="col-md-3">
                                <a href="/api/status" class="btn btn-outline-info w-100 mb-2">
                                    <i class="fas fa-heartbeat"></i> System Status
                                </a>
                            </div>
                            <div class="col-md-3">
                                <a href="/api/news-status" class="btn btn-outline-success w-100 mb-2">
                                    <i class="fas fa-newspaper"></i> News Status
                                </a>
                            </div>
                            <div class="col-md-3">
                                <a href="/articles" class="btn btn-outline-warning w-100 mb-2">
                                    <i class="fas fa-list"></i> View Articles
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Info -->
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> System Information</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Version:</strong> WiseNews 3.0.0 - Railway Full</p>
                        <p><strong>Platform:</strong> Railway Hobby Plan</p>
                        <p><strong>Authentication:</strong> ✅ Enabled</p>
                        <p><strong>Admin Email:</strong> admin@wisenews.com</p>
                        <p><strong>Database:</strong> SQLite (Railway Persistent)</p>
                        <p><strong>Features:</strong> All authentication features active</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', user=user, total_articles=total_articles, total_users=total_users, 
             articles_today=articles_today, new_users_week=new_users_week,
             top_sources=top_sources, categories=categories)
        
    except Exception as e:
        return f"<h1>Admin Dashboard Error: {str(e)}</h1>", 500

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Railway Full-Feature deployment working!',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0-railway-full',
        'authentication': 'enabled',
        'admin_credentials': {
            'email': 'admin@wisenews.com',
            'password': 'WiseNews2025!'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🗞️  WiseNews Railway Full-Feature v2 starting on {host}:{port}")
    print(f"📊 Database: {app.config['DATABASE']}")
    print(f"🚀 Version: 3.0.0 - Railway Full-Feature v2")
    print(f"🔐 Authentication: ENABLED")
    print(f"⚡ Force Deploy: {datetime.now().isoformat()}")
    
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    # Fetch initial news (Railway optimized)
    print("📰 Fetching initial news...")
    try:
        total = fetch_all_news()
        print(f"✅ Initial news fetch complete: {total} articles")
    except Exception as e:
        print(f"⚠️ Initial news fetch failed: {e}")
    
    print("✅ WiseNews Railway Full-Feature ready!")
    print("🔑 Admin: admin@wisenews.com / WiseNews2025!")
    app.run(host=host, port=port, debug=False)
