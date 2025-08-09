#!/usr/bin/env python3
"""
WiseNews - Railway-Compatible Complete System
Handles missing dependencies gracefully while providing full features
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime, timedelta
import json
import secrets
import bcrypt
from functools import wraps
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'

# Database configuration - use the correct database for Railway
DATABASE_PATH = 'news_database.db'

# Initialize core systems with graceful error handling
try:
    from server_optimizer import optimizer, cache_db_query, get_optimized_db_connection, return_optimized_db_connection
    OPTIMIZER_AVAILABLE = True
except ImportError:
    print("Server optimizer not available, using standard connections")
    OPTIMIZER_AVAILABLE = False
    
try:
    from api_security import api_manager
    from api_protection import require_api_key, anti_scraping_protection, browser_only
    API_SECURITY_AVAILABLE = True
except ImportError:
    print("API security modules not available, using basic protection")
    API_SECURITY_AVAILABLE = False

try:
    from user_auth import user_manager
    from auth_decorators import login_required, admin_required, get_current_user, get_user_ip, get_user_agent
    USER_AUTH_AVAILABLE = True
except ImportError:
    print("User auth modules not available, implementing basic auth")
    USER_AUTH_AVAILABLE = False

try:
    from subscription_manager import SubscriptionManager, subscription_required, api_access_required
    subscription_manager = SubscriptionManager()
    SUBSCRIPTION_AVAILABLE = True
except ImportError:
    print("Subscription manager not available, using free access")
    SUBSCRIPTION_AVAILABLE = False
    subscription_manager = None

# Basic auth decorators if modules not available
if not USER_AUTH_AVAILABLE:
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or not session.get('is_admin'):
                flash('Admin access required.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def get_current_user():
        if 'user_id' in session:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT id, email, is_admin FROM users WHERE id = ?', (session['user_id'],))
                user_data = cursor.fetchone()
                conn.close()
                if user_data:
                    return {'id': user_data[0], 'email': user_data[1], 'is_admin': user_data[2]}
            except:
                pass
        return None

# Database helper functions
def get_db_connection():
    """Get database connection with fallback"""
    if OPTIMIZER_AVAILABLE:
        return get_optimized_db_connection()
    else:
        return sqlite3.connect(DATABASE_PATH)

def return_db_connection(conn):
    """Return database connection"""
    if OPTIMIZER_AVAILABLE:
        return_optimized_db_connection(conn)
    else:
        conn.close()

# ============================================================================
# CORE ROUTES
# ============================================================================

@app.route('/')
def home():
    """Homepage with latest articles"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest articles
        cursor.execute('''
            SELECT id, title, summary, source, category, published_date 
            FROM articles 
            ORDER BY published_date DESC 
            LIMIT 10
        ''')
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2] or 'No summary available',
                'source': row[3],
                'category': row[4],
                'published_date': row[5]
            })
        
        return_db_connection(conn)
        
        # Render with embedded template
        return render_template_string(HOME_TEMPLATE, articles=articles)
        
    except Exception as e:
        print(f"Error loading homepage: {e}")
        return jsonify({'error': 'Unable to load articles'}), 500

@app.route('/articles')
def articles():
    """Articles page with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get articles with pagination
        cursor.execute('''
            SELECT id, title, summary, source, category, published_date, author
            FROM articles 
            ORDER BY published_date DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2] or 'No summary available',
                'source': row[3],
                'category': row[4],
                'published_date': row[5],
                'author': row[6] or 'Unknown'
            })
        
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        return_db_connection(conn)
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template_string(ARTICLES_TEMPLATE, 
                                    articles=articles,
                                    page=page,
                                    total_pages=total_pages,
                                    has_prev=has_prev,
                                    has_next=has_next,
                                    total=total)
        
    except Exception as e:
        print(f"Error loading articles: {e}")
        return jsonify({'error': 'Unable to load articles'}), 500

@app.route('/search')
def search():
    """Search functionality"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template_string(SEARCH_TEMPLATE, articles=[], query='')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in title and summary
        cursor.execute('''
            SELECT id, title, summary, source, category, published_date
            FROM articles 
            WHERE title LIKE ? OR summary LIKE ? OR content LIKE ?
            ORDER BY published_date DESC 
            LIMIT 50
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2] or 'No summary available',
                'source': row[3],
                'category': row[4],
                'published_date': row[5]
            })
        
        return_db_connection(conn)
        
        return render_template_string(SEARCH_TEMPLATE, articles=articles, query=query)
        
    except Exception as e:
        print(f"Error searching: {e}")
        return render_template_string(SEARCH_TEMPLATE, articles=[], query=query, error="Search failed")

@app.route('/category/<category_name>')
def category_articles(category_name):
    """Articles by category"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, summary, source, category, published_date
            FROM articles 
            WHERE category = ?
            ORDER BY published_date DESC 
            LIMIT 50
        ''', (category_name,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2] or 'No summary available',
                'source': row[3],
                'category': row[4],
                'published_date': row[5]
            })
        
        return_db_connection(conn)
        
        return render_template_string(CATEGORY_TEMPLATE, 
                                    articles=articles, 
                                    category=category_name.title())
        
    except Exception as e:
        print(f"Error loading category: {e}")
        return jsonify({'error': 'Unable to load category'}), 500

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password required.', 'error')
            return render_template_string(LOGIN_TEMPLATE)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, email, password_hash, is_admin FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['user_id'] = user[0]
                session['user_email'] = user[1]
                session['is_admin'] = bool(user[3])
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials.', 'error')
            
            return_db_connection(conn)
            
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password required.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered.', 'error')
                return render_template_string(REGISTER_TEMPLATE)
            
            # Create user
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (email, password_hash, is_admin, is_active, created_at)
                VALUES (?, ?, 0, 1, ?)
            ''', (email, password_hash, datetime.now()))
            
            conn.commit()
            return_db_connection(conn)
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user = get_current_user()
    
    # Get user's subscription if available
    subscription = None
    if SUBSCRIPTION_AVAILABLE:
        subscription = subscription_manager.get_user_subscription(user['id'])
    
    return render_template_string(DASHBOARD_TEMPLATE, user=user, subscription=subscription)

# ============================================================================
# SUBSCRIPTION ROUTES (if available)
# ============================================================================

@app.route('/subscription-plans')
@login_required
def subscription_plans():
    """Subscription plans page"""
    if not SUBSCRIPTION_AVAILABLE:
        flash('Subscription system not available.', 'error')
        return redirect(url_for('dashboard'))
    
    plans = subscription_manager.get_all_plans()
    user = get_current_user()
    current_subscription = subscription_manager.get_user_subscription(user['id'])
    
    return render_template_string(SUBSCRIPTION_PLANS_TEMPLATE, 
                                plans=plans, 
                                current_subscription=current_subscription)

@app.route('/my-subscription')
@login_required 
def my_subscription():
    """My subscription page"""
    if not SUBSCRIPTION_AVAILABLE:
        flash('Subscription system not available.', 'error')
        return redirect(url_for('dashboard'))
    
    user = get_current_user()
    subscription = subscription_manager.get_user_subscription(user['id'])
    daily_usage = subscription_manager.get_daily_usage(user['id']) if subscription else {}
    
    return render_template_string(MY_SUBSCRIPTION_TEMPLATE, 
                                subscription=subscription, 
                                daily_usage=daily_usage)

# ============================================================================
# LIVE EVENTS ROUTES (simplified)
# ============================================================================

@app.route('/live-events')
@login_required
def live_events():
    """Live events page"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get active live events
        cursor.execute('''
            SELECT id, event_name, description, category, status, created_at
            FROM live_events 
            WHERE status = 'live'
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'category': row[3],
                'status': row[4],
                'created_at': row[5]
            })
        
        return_db_connection(conn)
        
        return render_template_string(LIVE_EVENTS_TEMPLATE, events=events)
        
    except Exception as e:
        print(f"Error loading live events: {e}")
        return render_template_string(LIVE_EVENTS_TEMPLATE, events=[])

@app.route('/quick-updates')
@login_required
def quick_updates():
    """Quick updates page"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent notifications
        cursor.execute('''
            SELECT id, title, content, category, date_added, priority
            FROM notifications 
            ORDER BY date_added DESC 
            LIMIT 50
        ''')
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'category': row[3],
                'date_added': row[4],
                'priority': row[5]
            })
        
        return_db_connection(conn)
        
        return render_template_string(QUICK_UPDATES_TEMPLATE, notifications=notifications)
        
    except Exception as e:
        print(f"Error loading quick updates: {e}")
        return render_template_string(QUICK_UPDATES_TEMPLATE, notifications=[])

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        return_db_connection(conn)
        
        return jsonify({
            'status': 'online',
            'articles': article_count,
            'users': user_count,
            'features': {
                'subscription_system': SUBSCRIPTION_AVAILABLE,
                'user_auth': USER_AUTH_AVAILABLE,
                'api_security': API_SECURITY_AVAILABLE,
                'optimizer': OPTIMIZER_AVAILABLE
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/articles')
def api_articles():
    """API articles endpoint"""
    try:
        limit = request.args.get('limit', 20, type=int)
        category = request.args.get('category')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT id, title, summary, source, category, published_date
                FROM articles 
                WHERE category = ?
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT id, title, summary, source, category, published_date
                FROM articles 
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2],
                'source': row[3],
                'category': row[4],
                'published_date': row[5]
            })
        
        return_db_connection(conn)
        
        return jsonify({'articles': articles, 'count': len(articles)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories')
def api_categories():
    """API categories endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM articles 
            GROUP BY category 
            ORDER BY count DESC
        ''')
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'name': row[0],
                'count': row[1]
            })
        
        return_db_connection(conn)
        
        return jsonify({'categories': categories})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-events/active-count')
def api_live_events_count():
    """API live events count"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM live_events WHERE status = "live"')
        count = cursor.fetchone()[0]
        
        return_db_connection(conn)
        
        return jsonify({'count': count, 'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM live_events WHERE status = "live"')
        live_events_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE date_added > datetime("now", "-24 hours")')
        recent_notifications = cursor.fetchone()[0]
        
        return_db_connection(conn)
        
        stats = {
            'articles': article_count,
            'users': user_count,
            'live_events': live_events_count,
            'notifications_24h': recent_notifications
        }
        
        return render_template_string(ADMIN_TEMPLATE, stats=stats)
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        return jsonify({'error': 'Unable to load admin dashboard'}), 500

# ============================================================================
# TEMPLATES (Embedded for Railway compatibility)
# ============================================================================

HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>WiseNews - Your Complete News Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link" href="/articles">Articles</a>
                <a class="nav-link" href="/search">Search</a>
                {% if session.user_id %}
                    <a class="nav-link" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/logout">Logout</a>
                {% else %}
                    <a class="nav-link" href="/login">Login</a>
                    <a class="nav-link" href="/register">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">Latest News</h1>
                
                {% if articles %}
                    <div class="row">
                        {% for article in articles %}
                        <div class="col-md-6 mb-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">{{ article.title }}</h5>
                                    <p class="card-text">{{ article.summary[:150] }}...</p>
                                    <div class="d-flex justify-content-between">
                                        <small class="text-muted">
                                            <i class="fas fa-tag"></i> {{ article.category|title }}
                                        </small>
                                        <small class="text-muted">
                                            <i class="fas fa-clock"></i> {{ article.published_date }}
                                        </small>
                                    </div>
                                    <div class="mt-2">
                                        <small class="text-muted">
                                            <i class="fas fa-globe"></i> {{ article.source }}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> No articles available at the moment.
                    </div>
                {% endif %}
                
                <div class="text-center mt-4">
                    <a href="/articles" class="btn btn-primary">View All Articles</a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

ARTICLES_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Articles - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link active" href="/articles">Articles</a>
                <a class="nav-link" href="/search">Search</a>
                {% if session.user_id %}
                    <a class="nav-link" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/logout">Logout</a>
                {% else %}
                    <a class="nav-link" href="/login">Login</a>
                    <a class="nav-link" href="/register">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1 class="mb-4">All Articles <small class="text-muted">({{ total }} total)</small></h1>
        
        {% if articles %}
            {% for article in articles %}
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">{{ article.title }}</h5>
                    <p class="card-text">{{ article.summary }}</p>
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">
                                <i class="fas fa-tag"></i> {{ article.category|title }} |
                                <i class="fas fa-globe"></i> {{ article.source }}
                            </small>
                        </div>
                        <div class="col-md-6 text-end">
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> {{ article.published_date }}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
            
            <!-- Pagination -->
            {% if total_pages > 1 %}
            <nav>
                <ul class="pagination justify-content-center">
                    {% if has_prev %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page - 1 }}">Previous</a>
                        </li>
                    {% endif %}
                    
                    {% for p in range(1, total_pages + 1) %}
                        {% if p == page %}
                            <li class="page-item active">
                                <span class="page-link">{{ p }}</span>
                            </li>
                        {% else %}
                            <li class="page-item">
                                <a class="page-link" href="?page={{ p }}">{{ p }}</a>
                            </li>
                        {% endif %}
                    {% endfor %}
                    
                    {% if has_next %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page + 1 }}">Next</a>
                        </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
        {% else %}
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> No articles found.
            </div>
        {% endif %}
    </div>

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
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4>Login to WiseNews</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Don't have an account? <a href="/register">Register here</a></p>
                        </div>
                        
                        <div class="alert alert-info mt-3">
                            <strong>Admin Access:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Additional templates continue here but truncated for length...
REGISTER_TEMPLATE = '''<!DOCTYPE html><html><head><title>Register - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a></div></nav><div class="container mt-5"><div class="row justify-content-center"><div class="col-md-6"><div class="card"><div class="card-header"><h4>Register for WiseNews</h4></div><div class="card-body"><form method="POST"><div class="mb-3"><label for="email" class="form-label">Email</label><input type="email" class="form-control" id="email" name="email" required></div><div class="mb-3"><label for="password" class="form-label">Password</label><input type="password" class="form-control" id="password" name="password" required></div><button type="submit" class="btn btn-primary w-100">Register</button></form></div></div></div></div></div></body></html>'''

DASHBOARD_TEMPLATE = '''<!DOCTYPE html><html><head><title>Dashboard - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a><div class="navbar-nav ms-auto"><a class="nav-link" href="/">Home</a><a class="nav-link" href="/articles">Articles</a><a class="nav-link" href="/live-events">Live Events</a><a class="nav-link" href="/quick-updates">Quick Updates</a><a class="nav-link" href="/my-subscription">Subscription</a><a class="nav-link" href="/logout">Logout</a></div></div></nav><div class="container mt-4"><h1>Welcome, {{ user.email }}!</h1><div class="row mt-4"><div class="col-md-4"><div class="card"><div class="card-body text-center"><h5>Live Events</h5><a href="/live-events" class="btn btn-primary">View Events</a></div></div></div><div class="col-md-4"><div class="card"><div class="card-body text-center"><h5>Quick Updates</h5><a href="/quick-updates" class="btn btn-info">View Updates</a></div></div></div><div class="col-md-4"><div class="card"><div class="card-body text-center"><h5>My Subscription</h5><a href="/my-subscription" class="btn btn-success">Manage</a></div></div></div></div></div></body></html>'''

SEARCH_TEMPLATE = '''<!DOCTYPE html><html><head><title>Search - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a></div></nav><div class="container mt-4"><h1>Search Articles</h1><form method="GET" class="mb-4"><div class="input-group"><input type="text" class="form-control" name="q" value="{{ query }}" placeholder="Search articles..."><button class="btn btn-primary" type="submit">Search</button></div></form>{% if articles %}{% for article in articles %}<div class="card mb-3"><div class="card-body"><h5>{{ article.title }}</h5><p>{{ article.summary }}</p><small class="text-muted">{{ article.source }} - {{ article.category }}</small></div></div>{% endfor %}{% elif query %}<div class="alert alert-info">No articles found for "{{ query }}"</div>{% endif %}</div></body></html>'''

CATEGORY_TEMPLATE = '''<!DOCTYPE html><html><head><title>{{ category }} - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a></div></nav><div class="container mt-4"><h1>{{ category }} Articles</h1>{% for article in articles %}<div class="card mb-3"><div class="card-body"><h5>{{ article.title }}</h5><p>{{ article.summary }}</p><small class="text-muted">{{ article.source }} - {{ article.published_date }}</small></div></div>{% endfor %}</div></body></html>'''

LIVE_EVENTS_TEMPLATE = '''<!DOCTYPE html><html><head><title>Live Events - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a></div></nav><div class="container mt-4"><h1>Live Events</h1>{% if events %}{% for event in events %}<div class="card mb-3"><div class="card-body"><h5>{{ event.name }}</h5><p>{{ event.description }}</p><span class="badge bg-danger">{{ event.status|upper }}</span><small class="text-muted"> - {{ event.category }}</small></div></div>{% endfor %}{% else %}<div class="alert alert-info">No live events at the moment.</div>{% endif %}</div></body></html>'''

QUICK_UPDATES_TEMPLATE = '''<!DOCTYPE html><html><head><title>Quick Updates - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><nav class="navbar navbar-expand-lg navbar-dark bg-dark"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a></div></nav><div class="container mt-4"><h1>Quick Updates</h1>{% if notifications %}{% for notification in notifications %}<div class="card mb-2"><div class="card-body"><h6>{{ notification.title }}</h6><p class="mb-1">{{ notification.content }}</p><small class="text-muted">{{ notification.date_added }} - {{ notification.category }}</small></div></div>{% endfor %}{% else %}<div class="alert alert-info">No quick updates available.</div>{% endif %}</div></body></html>'''

SUBSCRIPTION_PLANS_TEMPLATE = '''<!DOCTYPE html><html><head><title>Subscription Plans - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><div class="container mt-4"><h1>Subscription Plans</h1><div class="row">{% for plan in plans %}<div class="col-md-4 mb-4"><div class="card"><div class="card-header text-center"><h4>{{ plan.display_name }}</h4><h2>${{ plan.price_monthly }}/month</h2></div><div class="card-body"><p>{{ plan.description }}</p><ul>{% for feature in plan.features %}<li>{{ feature }}</li>{% endfor %}</ul></div></div></div>{% endfor %}</div></div></body></html>'''

MY_SUBSCRIPTION_TEMPLATE = '''<!DOCTYPE html><html><head><title>My Subscription - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><div class="container mt-4"><h1>My Subscription</h1>{% if subscription %}<div class="card"><div class="card-body"><h4>{{ subscription.plan_display_name }}</h4><p>Status: <span class="badge bg-success">{{ subscription.status|title }}</span></p><p>Max Articles per Day: {{ subscription.max_articles_per_day if subscription.max_articles_per_day != -1 else "Unlimited" }}</p>{% if daily_usage %}<h5>Today's Usage</h5><ul><li>Articles Viewed: {{ daily_usage.articles_viewed or 0 }}</li><li>Searches: {{ daily_usage.searches_performed or 0 }}</li></ul>{% endif %}</div></div>{% else %}<div class="alert alert-info">No active subscription. <a href="/subscription-plans">View Plans</a></div>{% endif %}</div></body></html>'''

ADMIN_TEMPLATE = '''<!DOCTYPE html><html><head><title>Admin Dashboard - WiseNews</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"></head><body><div class="container mt-4"><h1>Admin Dashboard</h1><div class="row"><div class="col-md-3"><div class="card text-center"><div class="card-body"><h3>{{ stats.articles }}</h3><p>Articles</p></div></div></div><div class="col-md-3"><div class="card text-center"><div class="card-body"><h3>{{ stats.users }}</h3><p>Users</p></div></div></div><div class="col-md-3"><div class="card text-center"><div class="card-body"><h3>{{ stats.live_events }}</h3><p>Live Events</p></div></div></div><div class="col-md-3"><div class="card text-center"><div class="card-body"><h3>{{ stats.notifications_24h }}</h3><p>Notifications (24h)</p></div></div></div></div></div></body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
