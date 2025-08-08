from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
import hashlib

app = Flask(__name__)
app.secret_key = 'wisenews-secret-key-2025'

# Simple user database (in production, use a real database)
USERS = {
    'admin@wisenews.com': {
        'password_hash': hashlib.sha256('WiseNews2025!'.encode()).hexdigest(),
        'is_admin': True
    }
}

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>WiseNews - Authentication Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="text-center">
            <h1>🎉 WiseNews Authentication Working!</h1>
            <p class="lead">Render deployment with working login system</p>
            
            {% if session.get('user_email') %}
                <div class="alert alert-success">
                    <h3>✅ Login Successful!</h3>
                    <p>Welcome, {{ session.user_email }}!</p>
                    <p>Admin: {{ 'Yes' if session.get('is_admin') else 'No' }}</p>
                    <a href="/logout" class="btn btn-danger">Logout</a>
                </div>
            {% else %}
                <div class="alert alert-info">
                    <strong>Test Credentials:</strong><br>
                    Email: admin@wisenews.com<br>
                    Password: WiseNews2025!
                </div>
                <a href="/login" class="btn btn-primary btn-lg">Test Login Now</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS:
            user = USERS[email]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == user['password_hash']:
                session['user_email'] = email
                session['is_admin'] = user['is_admin']
                return redirect(url_for('home'))
        
        error = 'Invalid credentials'
    else:
        error = None
    
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
                        
                        {% if error %}
                            <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <div class="alert alert-info">
                            <strong>Test Credentials:</strong><br>
                            Email: admin@wisenews.com<br>
                            Password: WiseNews2025!
                        </div>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <input type="email" name="email" class="form-control" 
                                       placeholder="Email" value="admin@wisenews.com" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" name="password" class="form-control" 
                                       placeholder="Password" required>
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
    ''', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Simple Authentication Working!',
        'version': '1.0.0-simple',
        'authentication': 'ENABLED',
        'test_credentials': 'admin@wisenews.com / WiseNews2025!'
    })

if __name__ == '__main__':
    app.run(debug=True)

# Simplified news sources for Railway (fewer sources = less memory)
NEWS_SOURCES = {
    'bbc': {
        'name': 'BBC News',
        'rss': 'http://feeds.bbci.co.uk/news/rss.xml',
        'category': 'general'
    },
    'cnn': {
        'name': 'CNN',
        'rss': 'http://rss.cnn.com/rss/edition.rss',
        'category': 'general'
    },
    'techcrunch': {
        'name': 'TechCrunch',
        'rss': 'http://feeds.feedburner.com/TechCrunch/',
        'category': 'technology'
    }
}

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create tables
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
                fetch_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#007bff'
            )
        ''')
        
        # Insert default categories
        categories = [
            ('general', '#007bff'),
            ('technology', '#28a745'),
            ('business', '#ffc107'),
            ('sports', '#17a2b8'),
            ('health', '#dc3545'),
            ('science', '#6f42c1'),
            ('entertainment', '#fd7e14')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name, color)
            VALUES (?, ?)
        ''', categories)
        
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

def fetch_news_simple():
    """Simplified news fetching for Railway"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        for source_id, source_info in NEWS_SOURCES.items():
            try:
                print(f"📡 Fetching from {source_info['name']}...")
                
                response = urllib.request.urlopen(source_info['rss'], timeout=10)
                data = response.read()
                root = ET.fromstring(data)
                
                articles = []
                items = root.findall('.//item')[:5]  # Only 5 articles per source
                
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
                    except Exception as e:
                        pass  # Ignore duplicates
                
                print(f"✅ Fetched {len(articles)} articles from {source_info['name']}")
                
            except Exception as e:
                print(f"⚠️  Error fetching from {source_info['name']}: {e}")
        
        conn.commit()
        conn.close()
        print("🎉 News fetch complete!")
        
    except Exception as e:
        print(f"❌ News fetch failed: {e}")

@app.route('/')
def index():
    """Homepage with news articles"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, summary, url, source, category, published_date, image_url
            FROM articles 
            ORDER BY published_date DESC 
            LIMIT 20
        ''')
        
        articles = cursor.fetchall()
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
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-newspaper me-2"></i>WiseNews
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/register"><i class="fas fa-user-plus"></i> Register</a>
                <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1>🎉 <strong>WiseNews is Working on Railway!</strong></h1>
            <p class="lead">Smart News Aggregation Platform</p>
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i> <strong>Success!</strong> 
                Railway deployment is working perfectly!
            </div>
        </div>

        <div class="row">
            {% for article in articles %}
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">{{ article.title }}</h5>
                        <p class="card-text">{{ article.summary[:150] }}...</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">{{ article.source }}</small>
                            <a href="{{ article.url }}" target="_blank" class="btn btn-primary btn-sm">
                                Read More <i class="fas fa-external-link-alt"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
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
        ''', articles=articles)
        
    except Exception as e:
        return f"<h1>WiseNews</h1><p>App is running! Database error: {e}</p>"

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
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'WiseNews Render deployment with authentication!',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0-render-auth',
        'authentication': 'enabled',
        'admin_credentials': {
            'email': 'admin@wisenews.com',
            'password': 'WiseNews2025!'
        }
    })

@app.route('/api/debug')
def debug_auth():
    """Debug authentication system"""
    try:
        user_manager = user_auth.UserManager(app.config['DATABASE'])
        
        # Check if admin user exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = 'admin@wisenews.com'")
        admin_user = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'status': 'debug',
            'admin_user_exists': admin_user is not None,
            'admin_user_data': dict(admin_user) if admin_user else None,
            'database_file': app.config['DATABASE']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with working authentication"""
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
                return redirect(url_for('dashboard'))
            else:
                error_message = 'Invalid credentials'
        except Exception as e:
            error_message = f'Login error: {e}'
    else:
        error_message = None
    
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
                            <strong>Admin Credentials:</strong><br>
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
                        <form>
                            <div class="mb-3">
                                <input type="email" class="form-control" placeholder="Email" required>
                            </div>
                            <div class="mb-3">
                                <input type="password" class="form-control" placeholder="Password" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Register</button>
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🗞️  WiseNews Railway Optimized starting on {host}:{port}")
    print(f"📊 Database: {app.config['DATABASE']}")
    print(f"🚀 Version: 3.0.0 - Railway Optimized")
    
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    # Fetch initial news (simplified)
    print("📰 Fetching initial news...")
    try:
        fetch_news_simple()
    except Exception as e:
        print(f"⚠️ Initial news fetch failed: {e}")
    
    print("✅ WiseNews Railway Optimized ready!")
    app.run(host=host, port=port, debug=False)
