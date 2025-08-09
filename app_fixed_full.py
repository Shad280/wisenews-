#!/usr/bin/env python3
"""
WiseNews - Full Featured News Aggregation Platform
Reliable authentication + complete features
"""

from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
import bcrypt
from functools import wraps
import time
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

# Hardcoded working credentials
ADMIN_EMAIL = 'admin@wisenews.com'
ADMIN_PASSWORD = 'WiseNews2025!'

# RSS Sources for news aggregation
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
        
        # Create users table with simple schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create articles table
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
                views INTEGER DEFAULT 0
            )
        ''')
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                color TEXT DEFAULT '#007bff',
                description TEXT
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
        
        # Create admin user if it doesn't exist
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (ADMIN_EMAIL,))
        if cursor.fetchone()[0] == 0:
            password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name, is_admin, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ADMIN_EMAIL, password_hash, 'Admin', 'User', 1, 1))
            print("✅ Created admin user")
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user['is_admin']:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def fetch_rss_articles(max_articles=50):
    """Fetch articles from RSS sources"""
    articles = []
    
    for source_id, source_info in RSS_SOURCES.items():
        if not source_info['enabled']:
            continue
            
        try:
            print(f"Fetching from {source_info['name']}...")
            
            # Create request with headers
            req = urllib.request.Request(
                source_info['rss'],
                headers={'User-Agent': 'WiseNews/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Handle different RSS formats
            items = root.findall('.//item')
            if not items:
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:10]:  # Limit per source
                try:
                    # Extract article data
                    title = item.find('title')
                    title = title.text if title is not None else 'No Title'
                    
                    description = item.find('description')
                    if description is None:
                        description = item.find('summary')
                    summary = description.text if description is not None else ''
                    
                    link = item.find('link')
                    url = link.text if link is not None else ''
                    
                    author = item.find('author')
                    author = author.text if author is not None else source_info['name']
                    
                    # Parse publish date
                    pub_date = item.find('pubDate')
                    if pub_date is None:
                        pub_date = item.find('published')
                    
                    published_date = datetime.now()
                    if pub_date is not None:
                        try:
                            from dateutil import parser
                            published_date = parser.parse(pub_date.text)
                        except:
                            published_date = datetime.now()
                    
                    articles.append({
                        'title': title,
                        'summary': summary[:500],  # Limit summary length
                        'url': url,
                        'author': author,
                        'source': source_info['name'],
                        'category': source_info['category'],
                        'published_date': published_date,
                        'image_url': None
                    })
                    
                except Exception as item_error:
                    print(f"Error parsing item: {item_error}")
                    continue
                    
        except Exception as source_error:
            print(f"Error fetching from {source_info['name']}: {source_error}")
            continue
    
    return articles[:max_articles]

def save_articles_to_db(articles):
    """Save articles to database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        saved_count = 0
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (title, summary, url, author, source, category, image_url, published_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'],
                    article['summary'],
                    article['url'],
                    article['author'],
                    article['source'],
                    article['category'],
                    article['image_url'],
                    article['published_date']
                ))
                saved_count += 1
            except Exception as e:
                print(f"Error saving article: {e}")
                continue
        
        conn.commit()
        conn.close()
        print(f"✅ Saved {saved_count} articles to database")
        return saved_count
        
    except Exception as e:
        print(f"❌ Error saving articles: {e}")
        return 0

@app.route('/')
def home():
    """Homepage with news feed"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get recent articles
        cursor.execute('''
            SELECT title, summary, url, author, source, category, published_date, views
            FROM articles 
            ORDER BY published_date DESC 
            LIMIT 20
        ''')
        articles = cursor.fetchall()
        
        # Get categories
        cursor.execute('SELECT name, display_name, color FROM categories')
        categories = cursor.fetchall()
        
        conn.close()
        
        return render_template_string(HOME_TEMPLATE, 
                                    articles=articles, 
                                    categories=categories,
                                    user_logged_in='user_id' in session)
    except Exception as e:
        print(f"Home page error: {e}")
        return f"Error loading homepage: {e}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple, reliable login"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email and password are required', 'error')
                return redirect(url_for('login'))
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, password_hash, is_admin FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session['user_id'] = user['id']
                session['user_email'] = email
                session['is_admin'] = user['is_admin']
                
                flash('Login successful!', 'success')
                if user['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            flash(f'Login error: {e}', 'error')
            return redirect(url_for('login'))
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE, 
                                user_email=session.get('user_email'),
                                is_admin=session.get('is_admin', False))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT source, COUNT(*) as count FROM articles GROUP BY source')
        source_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template_string(ADMIN_TEMPLATE,
                                    article_count=article_count,
                                    user_count=user_count,
                                    source_stats=source_stats)
    except Exception as e:
        return f"Admin dashboard error: {e}", 500

@app.route('/fetch-news')
@admin_required
def fetch_news():
    """Fetch latest news articles"""
    try:
        articles = fetch_rss_articles()
        saved_count = save_articles_to_db(articles)
        flash(f'Fetched and saved {saved_count} articles', 'success')
    except Exception as e:
        flash(f'Error fetching news: {e}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/articles')
def api_articles():
    """API endpoint for articles"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category', '')
        
        if category:
            cursor.execute('''
                SELECT title, summary, url, author, source, category, published_date
                FROM articles 
                WHERE category = ?
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT title, summary, url, author, source, category, published_date
                FROM articles 
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (limit,))
        
        articles = cursor.fetchall()
        conn.close()
        
        return jsonify([dict(article) for article in articles])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Templates
HOME_TEMPLATE = '''
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
            padding: 60px 0;
        }
        .article-card {
            transition: transform 0.2s;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .category-badge {
            font-size: 0.8rem;
        }
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-newspaper"></i> WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                {% if user_logged_in %}
                    <a class="nav-link" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/logout">Logout</a>
                {% else %}
                    <a class="nav-link" href="/login">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container text-center">
            <h1 class="display-4 mb-4">
                <i class="fas fa-brain"></i> Welcome to WiseNews
            </h1>
            <p class="lead mb-4">
                Your intelligent news aggregation platform. Stay informed with the latest updates from trusted sources worldwide.
            </p>
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="d-flex flex-wrap justify-content-center gap-2 mb-4">
                        {% for category in categories %}
                        <span class="badge" style="background-color: {{ category.color }}; font-size: 0.9rem;">
                            {{ category.display_name }}
                        </span>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="container mt-3">
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    <!-- Articles Section -->
    <section class="py-5">
        <div class="container">
            <h2 class="text-center mb-5">Latest News</h2>
            
            {% if articles %}
                <div class="row">
                    {% for article in articles %}
                    <div class="col-md-6 col-lg-4 mb-4">
                        <div class="card article-card h-100">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="badge category-badge" style="background-color: {% for cat in categories %}{% if cat.name == article.category %}{{ cat.color }}{% endif %}{% endfor %}">
                                        {{ article.category.title() }}
                                    </span>
                                    <small class="text-muted">{{ article.source }}</small>
                                </div>
                                <h5 class="card-title">{{ article.title }}</h5>
                                <p class="card-text">{{ article.summary[:150] }}{% if article.summary|length > 150 %}...{% endif %}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <a href="{{ article.url }}" target="_blank" class="btn btn-primary btn-sm">
                                        Read More <i class="fas fa-external-link-alt"></i>
                                    </a>
                                    <small class="text-muted">
                                        <i class="fas fa-eye"></i> {{ article.views }}
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="text-center">
                    <div class="alert alert-info">
                        <h4><i class="fas fa-info-circle"></i> No Articles Yet</h4>
                        <p>Articles will appear here once the news feed is populated. 
                        {% if user_logged_in %}Admin users can fetch news from the dashboard.{% endif %}</p>
                    </div>
                </div>
            {% endif %}
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-white py-4 mt-5">
        <div class="container text-center">
            <p>&copy; 2025 WiseNews. Intelligent news aggregation platform.</p>
            <div class="mt-2">
                <span class="text-muted">Powered by Flask • Bootstrap • RSS Feeds</span>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .login-container {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div class="login-container d-flex align-items-center">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="card login-card">
                        <div class="card-body p-5">
                            <div class="text-center mb-4">
                                <i class="fas fa-newspaper fa-3x text-primary mb-3"></i>
                                <h2 class="card-title">WiseNews Login</h2>
                                <p class="text-muted">Access your news dashboard</p>
                            </div>

                            <!-- Flash Messages -->
                            {% with messages = get_flashed_messages(with_categories=true) %}
                                {% if messages %}
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                                            {{ message }}
                                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                        </div>
                                    {% endfor %}
                                {% endif %}
                            {% endwith %}

                            <div class="alert alert-info">
                                <h6><i class="fas fa-key"></i> Admin Credentials:</h6>
                                <p class="mb-1"><strong>Email:</strong> admin@wisenews.com</p>
                                <p class="mb-0"><strong>Password:</strong> WiseNews2025!</p>
                            </div>

                            <form method="POST">
                                <div class="mb-3">
                                    <label for="email" class="form-label">
                                        <i class="fas fa-envelope"></i> Email
                                    </label>
                                    <input type="email" class="form-control" id="email" name="email" 
                                           value="admin@wisenews.com" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">
                                        <i class="fas fa-lock"></i> Password
                                    </label>
                                    <input type="password" class="form-control" id="password" name="password" 
                                           value="WiseNews2025!" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">
                                    <i class="fas fa-sign-in-alt"></i> Login
                                </button>
                            </form>
                            
                            <div class="text-center mt-3">
                                <a href="/" class="text-decoration-none">
                                    <i class="fas fa-arrow-left"></i> Back to Homepage
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-newspaper"></i> WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Welcome, {{ user_email }}</span>
                {% if is_admin %}
                    <a class="nav-link" href="/admin">Admin Panel</a>
                {% endif %}
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1><i class="fas fa-tachometer-alt"></i> User Dashboard</h1>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5><i class="fas fa-user"></i> Account Information</h5>
                        <p><strong>Email:</strong> {{ user_email }}</p>
                        <p><strong>Role:</strong> {{ 'Administrator' if is_admin else 'User' }}</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5><i class="fas fa-newspaper"></i> Quick Actions</h5>
                        <a href="/" class="btn btn-primary">View News Feed</a>
                        {% if is_admin %}
                            <a href="/admin" class="btn btn-success">Admin Panel</a>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-newspaper"></i> WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1><i class="fas fa-cogs"></i> Admin Dashboard</h1>
        
        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Statistics -->
        <div class="row mt-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <h4><i class="fas fa-newspaper"></i> {{ article_count }}</h4>
                        <p>Total Articles</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h4><i class="fas fa-users"></i> {{ user_count }}</h4>
                        <p>Total Users</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h4><i class="fas fa-rss"></i> {{ source_stats|length }}</h4>
                        <p>News Sources</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <h4><i class="fas fa-sync"></i></h4>
                        <p>System Status: Online</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-download"></i> News Management</h5>
                    </div>
                    <div class="card-body">
                        <p>Fetch the latest news articles from RSS sources.</p>
                        <a href="/fetch-news" class="btn btn-primary">
                            <i class="fas fa-sync"></i> Fetch Latest News
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Source Statistics</h5>
                    </div>
                    <div class="card-body">
                        {% for source in source_stats %}
                            <div class="d-flex justify-content-between">
                                <span>{{ source.source }}</span>
                                <span class="badge bg-secondary">{{ source.count }} articles</span>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Starting WiseNews...")
    init_db()
    print("🔑 Admin login: admin@wisenews.com / WiseNews2025!")
    
    # Try to install dateutil for better date parsing
    try:
        import dateutil
    except ImportError:
        print("⚠️  dateutil not available - using basic date parsing")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
