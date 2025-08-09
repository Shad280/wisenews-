from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sqlite3
from datetime import datetime
import secrets

# Import server optimizer
from server_optimizer import optimizer, cache_db_query, get_optimized_db_connection, return_optimized_db_connection

# Import API security modules
from api_security import api_manager
from api_protection import require_api_key, anti_scraping_protection, browser_only

# Import user authentication modules
from user_auth import user_manager
from auth_decorators import login_required, admin_required, get_current_user, get_user_ip, get_user_agent

# Import subscription management
from subscription_manager import SubscriptionManager, subscription_required, api_access_required

# Import notification management
from notification_manager import NotificationManager, start_notification_processor

# Import live events management
from live_events_manager import live_events_manager

# Import enhanced live events manager (WebSocket-based)
try:
    from enhanced_live_events import EnhancedLiveEventsManager
    ENHANCED_LIVE_EVENTS_AVAILABLE = True
except ImportError:
    print("Enhanced live events not available. Using basic functionality.")
    EnhancedLiveEventsManager = None
    ENHANCED_LIVE_EVENTS_AVAILABLE = False

# Import quick updates manager
try:
    from quick_updates_manager import get_quick_updates_manager
    QUICK_UPDATES_AVAILABLE = True
except ImportError:
    print("Quick updates not available. Using basic functionality.")
    get_quick_updates_manager = None
    QUICK_UPDATES_AVAILABLE = False

# Import quick updates frontend
try:
    from quick_updates_frontend import inject_quick_updates_frontend
    QUICK_UPDATES_FRONTEND_AVAILABLE = True
except ImportError:
    print("Quick updates frontend not available.")
    inject_quick_updates_frontend = None
    QUICK_UPDATES_FRONTEND_AVAILABLE = False

# Import live events archiver
from live_events_archiver import live_events_archiver

# Import social media management
from social_routes import social_bp

# Import image management for articles
from image_manager import image_manager

# Import scraper protection
from scraper_protection import scraper_protection, anti_scraper_protection

# Import live feeds system
from live_feeds_routes import live_feeds_bp

# Import support chatbot system
from support_routes import support_bp

# Import performance optimizer
from app_performance_optimizer import optimize_app

import logging


def with_loading_screen(message="Loading...", min_delay=1000):
    """Decorator to show loading screen for slow operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # For AJAX requests, return loading status
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "loading", "message": message})
            
            # For regular requests, show loading screen briefly then redirect
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                
                # If operation was fast, no need for loading screen
                if elapsed < min_delay:
                    return result
                    
                # If operation was slow, it probably already rendered
                return result
                
            except Exception as e:
                # On error, show error page instead of loading screen
                logger.error(f"Error in {func.__name__}: {e}")
                return render_template('error.html', 
                                     error="An error occurred while loading the page.",
                                     details=str(e) if app.debug else None), 500
        
        return wrapper
    return decorator


app = Flask(__name__)

# Initialize SocketIO for real-time WebSocket connections
socketio = SocketIO(app, cors_allowed_origins="*", 
                   async_mode='gevent',
                   ping_timeout=60,
                   ping_interval=25,
                   logger=False,
                   engineio_logger=False)

# Load production configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object('production_config')
else:
    # Development configuration
    app.config['SECRET_KEY'] = 'wisenews-secure-key-2025'
    app.config['DEBUG'] = False  # Always disable debug for security
    app.config['TESTING'] = False

# Initialize caching
cache = Cache()
cache.init_app(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 1000
})

# Apply performance optimizations
app_optimizer = optimize_app(app)

# Create cache directory
os.makedirs('cache', exist_ok=True)
os.makedirs('logs', exist_ok=True)

app.config['UPLOADS_FOLDER'] = 'downloads'

# SECURITY: Disable debug mode in production
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Performance optimizations
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Compression middleware
def gzip_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Handle different response types from Flask
        from flask import make_response
        if not hasattr(response, 'content_type'):
            response = make_response(response)
        
        # Check if client accepts gzip
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return response
            
        # Only compress certain content types
        if hasattr(response, 'content_type') and response.content_type and response.content_type.startswith(('text/', 'application/json', 'application/javascript')):
            if hasattr(response, 'data') and len(response.data) > 1000:
                # Compress the response
                buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                    gz_file.write(response.data)
                
                response.data = buffer.getvalue()
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(response.data)
                
        return response
    return decorated_function

def get_db_connection():
    """Get a thread-safe database connection"""
    return sqlite3.connect('news_database.db', check_same_thread=False, timeout=30.0)

def close_db_connection(conn):
    """Safely close database connection"""
    if conn:
        try:
            conn.close()
        except Exception:
            pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SECURITY: Error handlers to prevent information disclosure
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors without exposing system information"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors without exposing system information"""
    logger.error(f"Internal server error: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors without exposing system information"""
    return render_template('errors/403.html'), 403

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions without exposing system information"""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return render_template('errors/500.html'), 500

# Initialize managers
subscription_manager = SubscriptionManager()
notification_manager = NotificationManager()

# Initialize enhanced live events manager (WebSocket-based)
enhanced_live_events = None
if ENHANCED_LIVE_EVENTS_AVAILABLE:
    try:
        enhanced_live_events = EnhancedLiveEventsManager(app, socketio)
        print("✅ Enhanced live events system initialized with WebSocket support")
    except Exception as e:
        print(f"❌ Failed to initialize enhanced live events: {e}")
        enhanced_live_events = None
else:
    print("ℹ️ Using basic live events system (enhanced features not available)")

# Initialize quick updates manager
quick_updates = None
if QUICK_UPDATES_AVAILABLE:
    try:
        quick_updates = get_quick_updates_manager(socketio)
        print("✅ Quick updates system initialized")
    except Exception as e:
        print(f"❌ Failed to initialize quick updates: {e}")
        quick_updates = None
else:
    print("ℹ️ Quick updates not available")

# ============================================================================
# WEBSOCKET EVENT HANDLERS (Enhanced Live Events)
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client WebSocket connection"""
    if enhanced_live_events:
        print(f'✅ WebSocket client connected: {request.sid}')
        emit('connection_confirmed', {'status': 'connected', 'timestamp': datetime.now().isoformat()})
    else:
        emit('connection_failed', {'status': 'enhanced_features_unavailable'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    if enhanced_live_events:
        print(f'❌ WebSocket client disconnected: {request.sid}')
        enhanced_live_events.handle_user_disconnect(request.sid)

@socketio.on('join_event')
def handle_join_event(data):
    """Handle user joining an event room"""
    if not enhanced_live_events:
        emit('error', {'message': 'Enhanced live events not available'})
        return
    
    event_id = data.get('event_id')
    user_id = data.get('user_id', 1)
    
    if event_id:
        try:
            enhanced_live_events.subscribe_user(user_id, event_id, request.sid)
            join_room(f'event_{event_id}')
            emit('subscription_confirmed', {
                'event_id': event_id,
                'status': 'subscribed',
                'timestamp': datetime.now().isoformat()
            })
            print(f"👤 User {user_id} subscribed to event {event_id}")
        except Exception as e:
            emit('error', {'message': f'Failed to join event: {str(e)}'})

@socketio.on('leave_event')
def handle_leave_event(data):
    """Handle user leaving an event room"""
    if not enhanced_live_events:
        emit('error', {'message': 'Enhanced live events not available'})
        return
    
    event_id = data.get('event_id')
    user_id = data.get('user_id', 1)
    
    if event_id:
        try:
            enhanced_live_events.unsubscribe_user(user_id, event_id)
            leave_room(f'event_{event_id}')
            emit('subscription_cancelled', {
                'event_id': event_id,
                'status': 'unsubscribed',
                'timestamp': datetime.now().isoformat()
            })
            print(f"👤 User {user_id} unsubscribed from event {event_id}")
        except Exception as e:
            emit('error', {'message': f'Failed to leave event: {str(e)}'})

@socketio.on('request_event_status')
def handle_event_status_request(data):
    """Handle request for current event status"""
    if not enhanced_live_events:
        emit('error', {'message': 'Enhanced live events not available'})
        return
    
    event_id = data.get('event_id')
    if event_id:
        try:
            status = enhanced_live_events.get_event_status(event_id)
            emit('event_status', status)
        except Exception as e:
            emit('error', {'message': f'Failed to get event status: {str(e)}'})

@socketio.on('ping')
def handle_ping():
    """Handle ping for connection health check"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

@socketio.on('join_room')
def handle_join_room(data):
    """Handle joining update rooms"""
    room = data.get('room')
    if room:
        join_room(room)
        emit('room_joined', {'room': room, 'timestamp': datetime.now().isoformat()})

@socketio.on('leave_room')  
def handle_leave_room(data):
    """Handle leaving update rooms"""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('room_left', {'room': room, 'timestamp': datetime.now().isoformat()})

@socketio.on('request_performance_metrics')
def handle_performance_metrics_request():
    """Handle request for performance metrics"""
    if quick_updates:
        metrics = quick_updates.get_performance_metrics()
        emit('performance_metrics', metrics)
    else:
        emit('performance_metrics', {'error': 'Quick updates not available'})

# ============================================================================

# Database helper functions for optimization
def get_db():
    """Get optimized database connection"""
    return get_optimized_db_connection()

def close_db(conn):
    """Return database connection to pool"""
    return return_optimized_db_connection(conn)

# Optimized database query decorator
def optimized_db_query(func):
    """Decorator for optimized database queries with connection pooling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db()
            result = func(conn, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Database query error in {func.__name__}: {e}")
            raise
        finally:
            if conn:
                close_db(conn)
    return wrapper

# Initialize server optimizer on startup
def initialize_optimizations():
    """Initialize server optimizations on first request"""
    try:
        optimizer.run_full_optimization()
        logger.info("Server optimizations initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize optimizations: {e}")

# Call initialization when app starts
try:
    if __name__ != "__main__":
        # Only run optimizations when imported as module
        initialize_optimizations()
except Exception as e:
    logger.warning(f"Optimization initialization skipped: {e}")

# Register blueprints
app.register_blueprint(social_bp)
app.register_blueprint(live_feeds_bp)
app.register_blueprint(support_bp)

# Custom Jinja2 filters
@app.template_filter('date_diff')
def date_diff_filter(date_string):
    """Calculate days difference from now"""
    if not date_string:
        return 0
    try:
        if isinstance(date_string, str):
            target_date = datetime.fromisoformat(date_string)
        else:
            target_date = date_string
        now = datetime.now()
        return (target_date - now).days
    except:
        return 0

# Template global functions
@app.template_global()
def has_real_time_notifications_access_template(user_id):
    """Template wrapper for has_real_time_notifications_access - returns only boolean"""
    has_access, _ = has_real_time_notifications_access(user_id)
    return has_access

# Auto-refresh configuration
AUTO_REFRESH_ENABLED = True
REFRESH_INTERVAL_MINUTES = 30  # Default: 30 minutes

def generate_content_hash(content):
    """Generate a hash of the article content for duplicate detection"""
    # Clean content for better duplicate detection
    cleaned_content = re.sub(r'\s+', ' ', content.lower().strip())
    # Remove common variations that don't affect content meaning
    cleaned_content = re.sub(r'[^\w\s]', '', cleaned_content)
    return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()

def generate_title_hash(title):
    """Generate a hash of the article title for duplicate detection"""
    cleaned_title = re.sub(r'[^\w\s]', '', title.lower().strip())
    return hashlib.md5(cleaned_title.encode('utf-8')).hexdigest()

def is_duplicate_article(title, content, cursor):
    """Check if article is a duplicate using multiple methods"""
    
    # Method 1: Exact title match
    cursor.execute('SELECT id FROM articles WHERE title = ?', (title,))
    if cursor.fetchone():
        return True, "Exact title match"
    
    # Method 2: Similar title (first 50 characters)
    title_prefix = title[:50]
    cursor.execute('SELECT id FROM articles WHERE title LIKE ?', (f'{title_prefix}%',))
    if cursor.fetchone():
        return True, "Similar title match"
    
    # Method 3: Content hash match
    content_hash = generate_content_hash(content)
    cursor.execute('SELECT id FROM articles WHERE content_hash = ?', (content_hash,))
    if cursor.fetchone():
        return True, "Content hash match"
    
    # Method 4: Title hash match (for titles with different punctuation)
    title_hash = generate_title_hash(title)
    cursor.execute('SELECT id, title FROM articles WHERE url_hash = ?', (title_hash,))
    existing = cursor.fetchone()
    if existing:
        return True, f"Title hash match with: {existing[1]}"
    
    # Method 5: Content similarity (first 100 characters)
    content_prefix = content[:100] if len(content) > 100 else content
    cursor.execute('SELECT id FROM articles WHERE content LIKE ?', (f'{content_prefix}%',))
    if cursor.fetchone():
        return True, "Content similarity match"
    
    return False, "No duplicate found"

# PWA routes
@app.route('/static/manifest.json')
def manifest():
    return send_file('static/manifest.json', mimetype='application/json')

@app.route('/static/sw.js')
def service_worker():
    response = make_response(send_file('static/sw.js'))
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/sitemap.xml')
def sitemap():
    return send_file('static/sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return send_file('static/robots.txt', mimetype='text/plain')

# Database setup
def init_db():
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_name TEXT,
            filename TEXT NOT NULL,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            keywords TEXT,
            category TEXT,
            read_status BOOLEAN DEFAULT FALSE,
            url_hash TEXT,
            content_hash TEXT
        )
    ''')
    
    # Check if new columns exist and add them if they don't
    cursor.execute("PRAGMA table_info(articles)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'url_hash' not in columns:
        cursor.execute('ALTER TABLE articles ADD COLUMN url_hash TEXT')
    
    if 'content_hash' not in columns:
        cursor.execute('ALTER TABLE articles ADD COLUMN content_hash TEXT')
    
    # Create indexes for faster duplicate checking
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON articles(title)')
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_hash ON articles(url_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON articles(content_hash)')
    except sqlite3.OperationalError:
        # Indexes might fail if columns don't exist yet, will be created on next run
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            results_count INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            bookmark_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')
    
    # Subscription system tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            description TEXT,
            price_monthly DECIMAL(10,2),
            price_yearly DECIMAL(10,2),
            features TEXT, -- JSON string of features
            max_articles_per_day INTEGER,
            max_searches_per_day INTEGER,
            max_bookmarks INTEGER,
            api_access BOOLEAN DEFAULT FALSE,
            priority_support BOOLEAN DEFAULT FALSE,
            advanced_filters BOOLEAN DEFAULT FALSE,
            export_data BOOLEAN DEFAULT FALSE,
            real_time_notifications BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active', -- active, cancelled, expired, trial
            trial_start_date DATETIME,
            trial_end_date DATETIME,
            subscription_start_date DATETIME,
            subscription_end_date DATETIME,
            auto_renew BOOLEAN DEFAULT TRUE,
            payment_method TEXT,
            stripe_subscription_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (plan_id) REFERENCES subscription_plans (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            articles_viewed INTEGER DEFAULT 0,
            searches_performed INTEGER DEFAULT 0,
            bookmarks_created INTEGER DEFAULT 0,
            api_requests INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subscription_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            currency TEXT DEFAULT 'USD',
            payment_method TEXT,
            stripe_payment_id TEXT,
            status TEXT NOT NULL, -- success, failed, pending, refunded
            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (subscription_id) REFERENCES user_subscriptions (id)
        )
    ''')
    
    # Notification system tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email_notifications BOOLEAN DEFAULT TRUE,
            push_notifications BOOLEAN DEFAULT FALSE,
            notification_frequency TEXT DEFAULT 'daily', -- instant, daily, weekly
            categories TEXT, -- JSON array of preferred categories
            keywords TEXT, -- JSON array of keywords to watch for
            sources TEXT, -- JSON array of preferred sources
            time_preference TEXT DEFAULT '09:00', -- Preferred notification time
            timezone TEXT DEFAULT 'UTC',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            p256dh_key TEXT NOT NULL,
            auth_key TEXT NOT NULL,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL, -- email, push
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            scheduled_time DATETIME NOT NULL,
            sent_time DATETIME,
            status TEXT DEFAULT 'pending', -- pending, sent, failed
            retry_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            read_status BOOLEAN DEFAULT FALSE,
            article_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')
    
    # Live Events system tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_type TEXT NOT NULL, -- sports, finance, conference, speech, breaking_news
            category TEXT NOT NULL, -- football, basketball, stocks, crypto, politics, etc.
            status TEXT DEFAULT 'upcoming', -- upcoming, live, completed, cancelled
            start_time DATETIME,
            end_time DATETIME,
            venue TEXT,
            description TEXT,
            external_id TEXT, -- ID from external API
            data_source TEXT, -- API source name
            metadata TEXT, -- JSON for additional data
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_event_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            update_type TEXT NOT NULL, -- goal, score, quote, price_change, announcement
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            importance REAL DEFAULT 0.5, -- 0-1 scale for notification priority
            metadata TEXT, -- JSON for structured data (scores, prices, etc.)
            FOREIGN KEY (event_id) REFERENCES live_events (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_event_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            notification_types TEXT, -- JSON array: ["all", "major", "final"] 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (event_id) REFERENCES live_events (id),
            UNIQUE(user_id, event_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            icon TEXT, -- Font awesome icon class
            api_endpoint TEXT, -- External API endpoint
            api_key_required BOOLEAN DEFAULT FALSE,
            update_interval INTEGER DEFAULT 60, -- seconds
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Initialize default subscription plans
    cursor.execute("SELECT COUNT(*) FROM subscription_plans")
    result = cursor.fetchone()
    if result and result[0] == 0:
        # Insert default plans
        plans = [
            ('free', 'Free Trial', 'Perfect for trying out WiseNews', 0.00, 0.00, 
             '["7-day free trial", "Up to 10 articles per day", "Basic search", "5 bookmarks", "Email support", "Daily notifications only"]',
             10, 5, 5, False, False, False, False, False, True),
            ('standard', 'Standard', 'Great for regular news consumption', 5.99, 59.99,
             '["Unlimited articles", "Advanced search & filters", "50 bookmarks", "Priority email support", "Export articles", "Daily notifications only"]',
             -1, 50, 50, False, True, True, True, False, True),
            ('premium', 'Premium', 'Everything you need for professional news monitoring', 9.99, 99.99,
             '["Everything in Standard", "API access with 1000 requests/day", "Priority support", "Advanced analytics", "Custom categories", "Real-time notifications & alerts"]',
             -1, -1, -1, True, True, True, True, True, True)
        ]
        
        cursor.executemany('''
            INSERT INTO subscription_plans 
            (name, display_name, description, price_monthly, price_yearly, features, 
             max_articles_per_day, max_searches_per_day, max_bookmarks, api_access, 
             priority_support, advanced_filters, export_data, real_time_notifications, is_active) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', plans)
    
    # Add real_time_notifications column if it doesn't exist
    cursor.execute("PRAGMA table_info(subscription_plans)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'real_time_notifications' not in columns:
        cursor.execute('ALTER TABLE subscription_plans ADD COLUMN real_time_notifications BOOLEAN DEFAULT FALSE')
        # Update existing plans
        cursor.execute("UPDATE subscription_plans SET real_time_notifications = FALSE WHERE name IN ('free', 'standard')")
        cursor.execute("UPDATE subscription_plans SET real_time_notifications = TRUE WHERE name = 'premium'")
    
    # Update existing plan prices (for price changes)
    cursor.execute("UPDATE subscription_plans SET price_monthly = 5.99, price_yearly = 59.99 WHERE name = 'standard'")
    cursor.execute("UPDATE subscription_plans SET price_monthly = 9.99, price_yearly = 99.99 WHERE name = 'premium'")
    
    # Initialize event categories
    cursor.execute("SELECT COUNT(*) FROM event_categories")
    result = cursor.fetchone()
    if result and result[0] == 0:
        categories = [
            ('football', 'Football/Soccer', 'sports', 'fas fa-futbol', None, False, 30),
            ('basketball', 'Basketball', 'sports', 'fas fa-basketball-ball', None, False, 30),
            ('tennis', 'Tennis', 'sports', 'fas fa-table-tennis', None, False, 60),
            ('baseball', 'Baseball', 'sports', 'fas fa-baseball-ball', None, False, 60),
            ('stocks', 'Stock Market', 'finance', 'fas fa-chart-line', None, False, 60),
            ('crypto', 'Cryptocurrency', 'finance', 'fab fa-bitcoin', None, False, 30),
            ('forex', 'Forex Markets', 'finance', 'fas fa-dollar-sign', None, False, 60),
            ('politics', 'Political Events', 'conference', 'fas fa-landmark', None, False, 300),
            ('tech_conference', 'Tech Conferences', 'conference', 'fas fa-microchip', None, False, 300),
            ('earnings', 'Earnings Calls', 'conference', 'fas fa-building', None, False, 300),
            ('breaking_news', 'Breaking News', 'breaking_news', 'fas fa-exclamation-triangle', None, False, 60)
        ]
        
        cursor.executemany('''
            INSERT INTO event_categories 
            (name, display_name, event_type, icon, api_endpoint, api_key_required, update_interval) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', categories)
    
    conn.commit()
    conn.close()

def extract_keywords(text):
    """Extract keywords from article content"""
    # Remove common words and extract meaningful terms
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that', 'these', 'those', 'a', 'an', 'some', 'any', 'all', 'each', 'every', 'no', 'not', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once'}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered_words = [word for word in words if word not in common_words]
    
    # Get most common keywords
    word_counts = Counter(filtered_words)
    keywords = [word for word, count in word_counts.most_common(10)]
    
    return ', '.join(keywords)

def categorize_article(title, content):
    """Automatically categorize articles based on content"""
    title_content = (title + ' ' + content).lower()
    
    categories = {
        'Business': ['business', 'market', 'economy', 'finance', 'stock', 'trading', 'investment', 'bitcoin', 'crypto', 'currency', 'bank', 'financial'],
        'Technology': ['technology', 'tech', 'ai', 'artificial intelligence', 'software', 'computer', 'digital', 'cyber', 'data', 'internet'],
        'Politics': ['politics', 'political', 'government', 'election', 'vote', 'congress', 'senate', 'president', 'policy', 'law'],
        'Health': ['health', 'medical', 'disease', 'virus', 'vaccine', 'hospital', 'doctor', 'treatment', 'drug', 'medicine'],
        'Science': ['science', 'research', 'study', 'discovery', 'experiment', 'climate', 'environment', 'space', 'nasa'],
        'Sports': ['sports', 'game', 'team', 'player', 'match', 'championship', 'league', 'football', 'basketball', 'soccer'],
        'Entertainment': ['entertainment', 'movie', 'film', 'music', 'celebrity', 'actor', 'actress', 'show', 'television', 'tv'],
        'World': ['world', 'international', 'global', 'country', 'nation', 'war', 'conflict', 'peace', 'diplomatic']
    }
    
    category_scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in title_content)
        category_scores[category] = score
    
    if category_scores:
        return max(category_scores, key=category_scores.get)
    return 'General'

def has_real_time_notifications_access(user_id):
    """Check if user has access to real-time notifications based on their subscription"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Get user's current subscription and plan details
        cursor.execute('''
            SELECT sp.real_time_notifications, us.status, us.trial_end_date, us.subscription_end_date
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = ? AND us.status IN ('active', 'trial')
            ORDER BY us.created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # No active subscription - no access
            return False, "No active subscription found"
        
        has_feature, status, trial_end, subscription_end = result
        
        # Check if subscription is still valid
        now = datetime.now()
        if status == 'trial':
            if trial_end and datetime.fromisoformat(trial_end) < now:
                return False, "Free trial has expired"
        elif status == 'active':
            if subscription_end and datetime.fromisoformat(subscription_end) < now:
                return False, "Subscription has expired"
        
        # Check if plan includes real-time notifications
        if not has_feature:
            return False, "Your current plan doesn't include real-time notifications. Upgrade to Premium for instant alerts!"
        
        return True, "Real-time notifications enabled"
        
    except Exception as e:
        logger.error(f"Error checking real-time notifications access: {e}")
        return False, "Error checking subscription status"

def load_articles_to_db():
    """Load articles from files into database with duplicate detection"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Get all text files in downloads directory
    downloads_dir = 'downloads'
    if not os.path.exists(downloads_dir):
        conn.close()
        return {'added': 0, 'duplicates': 0, 'errors': 0, 'total_files': 0}
    
    files = [f for f in os.listdir(downloads_dir) if f.endswith('.txt')]
    
    articles_added = 0
    duplicates_skipped = 0
    errors = 0
    
    print(f"📚 Processing {len(files)} files for database import...")
    
    for filename in files:
        filepath = os.path.join(downloads_dir, filename)
        
        # Check if file already processed by filename
        cursor.execute('SELECT id FROM articles WHERE filename = ?', (filename,))
        if cursor.fetchone():
            continue  # Skip files already in database
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                print(f"⚠️  Empty file skipped: {filename}")
                continue
                
            # Extract source information from filename
            source_type = "RSS"
            source_name = "Unknown"
            
            if filename.startswith("RSS_") or filename.startswith("RSS__"):
                source_type = "RSS"
                if "__" in filename:
                    source_name = filename.split("__")[1] if len(filename.split("__")) > 1 else "RSS Feed"
                else:
                    source_name = "RSS Feed"
            elif filename.startswith("TW_") or filename.startswith("TWITTER__"):
                source_type = "Twitter"
                source_name = "Twitter"
            elif filename.startswith("YT_") or filename.startswith("YOUTUBE__"):
                source_type = "YouTube"
                source_name = "YouTube"
            
            # Extract title from filename or content
            title = filename.replace('.txt', '')
            # Remove prefixes
            for prefix in ['RSS__', 'RSS_', 'TW_', 'TWITTER__', 'YT_', 'YOUTUBE__']:
                if title.startswith(prefix):
                    title = title[len(prefix):]
                    break
            
            title = title.replace('_', ' ')[:200]  # Limit title length
            
            if not title.strip():
                title = content[:50] + '...' if len(content) > 50 else content
            
            # Check for duplicates using multiple methods
            is_duplicate, duplicate_reason = is_duplicate_article(title, content, cursor)
            
            if is_duplicate:
                print(f"🔄 Duplicate skipped: {title[:50]}... ({duplicate_reason})")
                duplicates_skipped += 1
                continue
            
            # Generate hashes for future duplicate detection
            content_hash = generate_content_hash(content)
            title_hash = generate_title_hash(title)
            
            keywords = extract_keywords(content)
            category = categorize_article(title, content)
            
            # Insert new article
            cursor.execute('''
                INSERT INTO articles (title, content, source_type, source_name, filename, file_path, keywords, category, url_hash, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, content, source_type, source_name, filename, filepath, keywords, category, title_hash, content_hash))
            
            # Get the newly inserted article ID
            article_id = cursor.lastrowid
            
            # Trigger quick update for new article
            if quick_updates:
                try:
                    article_data = {
                        'id': article_id,
                        'title': title,
                        'content': content,
                        'category': category,
                        'source_name': source_name,
                        'source_type': source_type,
                        'date_added': datetime.now().isoformat(),
                        'keywords': keywords.split(',') if keywords else []
                    }
                    quick_updates.add_quick_update('new_article', article_data, 'high')
                except Exception as e:
                    logger.warning(f"Failed to trigger quick update for article {article_id}: {e}")
            
            # Create article data for notifications
            article_data = {
                'id': article_id,
                'title': title,
                'content': content,
                'category': category,
                'source_name': source_name,
                'url': filepath,
                'keywords': keywords.split(',') if keywords else []
            }
            
            # Trigger notifications for this new article
            trigger_article_notifications(article_data)
            
            # Process article for relevant images (events, people, etc.)
            try:
                image_manager.process_article_for_images(article_id, title, content, category)
            except Exception as e:
                logger.warning(f"Failed to process images for article {article_id}: {e}")
            
            articles_added += 1
            print(f"✅ Added: {title[:50]}...")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            errors += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"""
📊 WiseNews Import Summary:
✅ New articles added: {articles_added}
🔄 Duplicates skipped: {duplicates_skipped}
❌ Errors encountered: {errors}
📁 Total files processed: {len(files)}
""")
    
    return {
        'added': articles_added,
        'duplicates': duplicates_skipped,
        'errors': errors,
        'total_files': len(files)
    }

@app.route('/')
@browser_only
@anti_scraping_protection
def index():
    """Main route - Shows landing page for new users, dashboard for authenticated users"""
    # Check if user is authenticated
    session_token = session.get('session_token')
    if session_token and user_manager.validate_session(session_token):
        # Authenticated user - redirect to dashboard
        return redirect(url_for('dashboard'))
    else:
        # New/unauthenticated user - show landing page
        return render_template('landing.html')

@app.route('/dashboard')
@login_required
@browser_only
@anti_scraping_protection
# @cache.memoize(timeout=60)  # Cache disabled temporarily
@gzip_response
def dashboard():
    """User dashboard - Protected from scraping and requires authentication"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    # Use cached data for performance
    cache_key = f"dashboard_data_{user_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render_template('dashboard.html', **cached_data)
    
    # Use direct SQLite connection to avoid thread issues
    conn = sqlite3.connect('news_database.db', timeout=30.0)
    cursor = conn.cursor()
    
    try:
        # Get statistics with optimized queries
        cursor.execute('SELECT COUNT(*) FROM articles WHERE is_deleted = 0')
        result = cursor.fetchone()
        total_articles = result[0] if result else 0
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE date_added >= date("now", "-1 day") AND is_deleted = 0')
        result = cursor.fetchone()
        today_articles = result[0] if result else 0
        
        # Use more efficient queries with indexes
        cursor.execute('''
            SELECT source_type, COUNT(*) 
            FROM articles 
            WHERE is_deleted = 0 
            GROUP BY source_type 
            LIMIT 10
        ''')
        source_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM articles 
            WHERE is_deleted = 0 
            GROUP BY category 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        ''')
        category_stats = cursor.fetchall()
        
        # Get recent articles with limit - exclude ongoing live events
        cursor.execute('''
            SELECT id, title, source_type, category, date_added, read_status 
            FROM articles 
            WHERE is_deleted = 0 
            AND (source_type != 'live_event' OR 
                 (source_type = 'live_event' AND 
                  CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                  (SELECT id FROM live_events WHERE status = 'completed')))
            ORDER BY date_added DESC 
            LIMIT 10
        ''')
        recent_articles = cursor.fetchall()
        
        # Get user's reading statistics efficiently
        user_stats = {
            'articles_read': 0,
            'bookmarks': 0,
            'searches': 0,
            'last_login': user.get('last_login') if user else None
        }
        
        # Get image statistics efficiently
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT article_id) 
                FROM article_images 
                WHERE is_deleted = 0
            """)
            result = cursor.fetchone()
            articles_with_images = result[0] if result else 0
            
            articles_without_images = max(0, total_articles - articles_with_images)
            
            cursor.execute("SELECT COUNT(*) FROM article_images WHERE is_deleted = 0")
            result = cursor.fetchone()
            total_images = result[0] if result else 0
        except Exception as e:
            logger.warning(f"Image statistics error: {e}")
            articles_with_images = 0
            articles_without_images = total_articles
            total_images = 0
        
    finally:
        conn.close()
    
    # Get subscription information
    subscription = None
    daily_usage = None
    if user_id:
        subscription = subscription_manager.get_user_subscription(user_id)
        daily_usage = subscription_manager.get_daily_usage(user_id)
    
    # Get quick updates performance metrics
    quick_updates_metrics = {}
    if quick_updates:
        try:
            quick_updates_metrics = quick_updates.get_performance_metrics()
        except Exception as e:
            logger.warning(f"Failed to get quick updates metrics: {e}")
    
    # Inject quick updates frontend if available
    quick_updates_frontend_code = ""
    if QUICK_UPDATES_FRONTEND_AVAILABLE and inject_quick_updates_frontend:
        try:
            quick_updates_frontend_code = inject_quick_updates_frontend()
        except Exception as e:
            logger.warning(f"Failed to inject quick updates frontend: {e}")
    
    # Prepare template data
    template_data = {
        'user': user,
        'user_stats': user_stats,
        'total_articles': total_articles,
        'today_articles': today_articles,
        'recent_articles': recent_articles,
        'source_stats': source_stats,
        'category_stats': category_stats,
        'articles_with_images': articles_with_images,
        'articles_without_images': articles_without_images,
        'total_images': total_images,
        'subscription': subscription,
        'daily_usage': daily_usage,
        'quick_updates_metrics': quick_updates_metrics,
        'quick_updates_frontend': quick_updates_frontend_code,
        'quick_updates_enabled': QUICK_UPDATES_AVAILABLE
    }
    
    # Cache the data for 2 minutes
    cache.set(cache_key, template_data, timeout=120)
    
    return render_template('dashboard.html', **template_data)
    
    return render_template('dashboard.html', 
                         user=user,
                         user_stats=user_stats,
                         total_articles=total_articles,
                         today_articles=today_articles,
                         source_stats=source_stats,
                         category_stats=category_stats,
                         recent_articles=recent_articles,
                         subscription=subscription,
                         daily_usage=daily_usage,
                         articles_with_images=articles_with_images,
                         articles_without_images=articles_without_images,
                         total_images=total_images)

@app.route('/about')
def about():
    """About page with app description"""
    return render_template('about.html')

@app.route('/terms')
def terms():
    """Terms and Conditions page"""
    return render_template('terms.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy_policy.html')

@app.route('/cookie-policy')
def cookie_policy():
    """Cookie Policy page"""
    return render_template('cookie_policy.html')

@app.route('/articles')
@anti_scraper_protection
@gzip_response
def articles():
    """Browse all articles with pagination and filtering - protected from scraping"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    source_filter = request.args.get('source', '')
    category_filter = request.args.get('category', '')
    read_filter = request.args.get('read_status', '')
    
    # Create cache key based on parameters
    cache_key = f"articles_p{page}_s{source_filter}_c{category_filter}_r{read_filter}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return render_template('articles.html', **cached_result)
    
    conn = get_db_connection()
    if not conn:
        return render_template('articles.html', articles=[], error="Database connection failed")
    cursor = conn.cursor()
    
    try:
        # Build query with filters - add is_deleted check and exclude ongoing live events
        where_conditions = ['is_deleted = 0']
        params = []
        
        # Exclude articles from ongoing live events (only show completed live events)
        where_conditions.append('''
            (source_type != 'live_event' OR 
             (source_type = 'live_event' AND 
              CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
              (SELECT id FROM live_events WHERE status = 'completed')))
        ''')
        
        if source_filter:
            where_conditions.append('source_type = ?')
            params.append(source_filter)
        
        if category_filter:
            where_conditions.append('category = ?')
            params.append(category_filter)
        
        if read_filter:
            where_conditions.append('read_status = ?')
            params.append(read_filter == 'true')
        
        where_clause = 'WHERE ' + ' AND '.join(where_conditions)
        
        # Get total count efficiently
        cursor.execute(f'SELECT COUNT(*) FROM articles {where_clause}', params)
        result = cursor.fetchone()
        total = result[0] if result else 0
        
        # Get articles for current page
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, title, source_type, source_name, category, date_added, read_status, keywords
            FROM articles 
            {where_clause}
            ORDER BY date_added DESC 
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        articles_data = cursor.fetchall()
        
        # Get unique sources and categories for filters (cached separately)
        sources_cache_key = "article_sources"
        sources = cache.get(sources_cache_key)
        if not sources:
            cursor.execute('SELECT DISTINCT source_type FROM articles WHERE is_deleted = 0 ORDER BY source_type')
            sources = [row[0] for row in cursor.fetchall()]
            cache.set(sources_cache_key, sources, timeout=300)  # Cache for 5 minutes
        
        categories_cache_key = "article_categories"
        categories = cache.get(categories_cache_key)
        if not categories:
            cursor.execute('SELECT DISTINCT category FROM articles WHERE is_deleted = 0 ORDER BY category')
            categories = [row[0] for row in cursor.fetchall()]
            cache.set(categories_cache_key, categories, timeout=300)  # Cache for 5 minutes
        
    finally:
        close_db(conn)
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page
    
    # Prepare template data
    template_data = {
        'articles': articles_data,
        'page': page,
        'total_pages': total_pages,
        'total': total,
        'sources': sources,
        'categories': categories,
        'current_source': source_filter,
        'current_category': category_filter,
        'current_read_status': read_filter
    }
    
    # Cache the result for 2 minutes
    cache.set(cache_key, template_data, timeout=120)
    
    return render_template('articles.html', **template_data)

@app.route('/article/<int:article_id>')
def view_article(article_id):
    """View individual article with anti-scraping protection"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, source_type, source_name, filename, 
                   date_added, keywords, category, read_status
            FROM articles 
            WHERE id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            return "Article not found", 404
        
        # Handle unicode content safely
        try:
            # Ensure content is properly decoded and safe for display
            processed_article = list(article)
            if processed_article[2]:  # content
                processed_article[2] = str(processed_article[2]).encode('utf-8', errors='ignore').decode('utf-8')
            if processed_article[1]:  # title
                processed_article[1] = str(processed_article[1]).encode('utf-8', errors='ignore').decode('utf-8')
            article = tuple(processed_article)
        except Exception as encoding_error:
            logger.error(f"Unicode encoding error for article {article_id}: {encoding_error}")
            # Continue with original article if encoding fails
        
        # Mark as read
        cursor.execute('UPDATE articles SET read_status = TRUE WHERE id = ?', (article_id,))
        conn.commit()
        conn.close()
        
        return render_template('article.html', article=article)
        
    except Exception as e:
        logger.error(f"Error viewing article {article_id}: {e}")
        if 'conn' in locals():
            conn.close()
        return "Internal server error", 500

@app.route('/search')
@anti_scraper_protection
def search():
    """Search articles with anti-scraping protection"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if not query:
        return render_template('search.html', query='', articles=[], total=0)
    
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Record search
    cursor.execute('INSERT INTO search_history (query) VALUES (?)', (query,))
    
    # Search in title, content, and keywords - exclude ongoing live events
    search_query = f'%{query}%'
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE (title LIKE ? OR content LIKE ? OR keywords LIKE ?)
        AND (source_type != 'live_event' OR 
             (source_type = 'live_event' AND 
              CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
              (SELECT id FROM live_events WHERE status = 'completed')))
    ''', (search_query, search_query, search_query))
    
    total = cursor.fetchone()[0]
    
    # Update search history with result count
    cursor.execute('UPDATE search_history SET results_count = ? WHERE id = last_insert_rowid()', (total,))
    
    # Get search results - exclude ongoing live events
    offset = (page - 1) * per_page
    cursor.execute('''
        SELECT id, title, source_type, source_name, category, date_added, 
               SUBSTR(content, 1, 200) as preview
        FROM articles 
        WHERE (title LIKE ? OR content LIKE ? OR keywords LIKE ?)
        AND (source_type != 'live_event' OR 
             (source_type = 'live_event' AND 
              CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
              (SELECT id FROM live_events WHERE status = 'completed')))
        ORDER BY date_added DESC
        LIMIT ? OFFSET ?
    ''', (search_query, search_query, search_query, per_page, offset))
    
    articles_data = cursor.fetchall()
    conn.commit()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('search.html',
                         query=query,
                         articles=articles_data,
                         page=page,
                         total_pages=total_pages,
                         total=total)

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Articles by source
    cursor.execute('SELECT source_type, COUNT(*) FROM articles GROUP BY source_type')
    source_data = cursor.fetchall()
    
    # Articles by category
    cursor.execute('SELECT category, COUNT(*) FROM articles GROUP BY category ORDER BY COUNT(*) DESC')
    category_data = cursor.fetchall()
    
    # Articles by date (last 7 days)
    cursor.execute('''
        SELECT DATE(date_added) as date, COUNT(*) 
        FROM articles 
        WHERE date_added >= date('now', '-7 days')
        GROUP BY DATE(date_added)
        ORDER BY date
    ''')
    daily_data = cursor.fetchall()
    
    # Top keywords
    cursor.execute('SELECT keywords FROM articles WHERE keywords IS NOT NULL')
    all_keywords = cursor.fetchall()
    
    # Parse keywords and count
    keyword_counter = Counter()
    for row in all_keywords:
        if row[0]:
            keywords = [k.strip() for k in row[0].split(',')]
            keyword_counter.update(keywords)
    
    top_keywords = keyword_counter.most_common(20)
    
    # Recent searches
    cursor.execute('''
        SELECT query, COUNT(*) as count, MAX(timestamp) as last_searched
        FROM search_history 
        GROUP BY query 
        ORDER BY count DESC, last_searched DESC 
        LIMIT 10
    ''')
    search_stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('analytics.html',
                         source_data=source_data,
                         category_data=category_data,
                         daily_data=daily_data,
                         top_keywords=top_keywords,
                         search_stats=search_stats)

@app.route('/api/run_scraper', methods=['POST'])
def run_scraper():
    """API endpoint to run the news scraper"""
    def run_scraper_background():
        try:
            import subprocess
            result = subprocess.run(['python', 'news_aggregator.py'], 
                                  capture_output=True, text=True, cwd='.')
            
            # Reload articles into database after scraping
            time.sleep(2)  # Wait for files to be written
            load_articles_to_db()
            
        except Exception as e:
            print(f"Error running scraper: {e}")
    
    # Run scraper in background thread
    thread = threading.Thread(target=run_scraper_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'News scraper started. Check back in a few minutes.'})

@app.route('/api/process_images', methods=['POST'])
@login_required
def process_article_images():
    """API endpoint to process articles for relevant images"""
    try:
        # Get parameters
        data = request.get_json() if request.is_json else {}
        article_id = data.get('article_id')
        bulk_process = data.get('bulk_process', False)
        limit = data.get('limit', 50)
        
        if article_id:
            # Process specific article
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('SELECT title, content, category FROM news WHERE id = ?', (article_id,))
            article = cursor.fetchone()
            conn.close()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404
            
            success = image_manager.process_article_for_images(
                article_id, article[0], article[1], article[2]
            )
            
            return jsonify({
                'success': success,
                'message': f'Image processing {"completed" if success else "failed"} for article {article_id}'
            })
            
        elif bulk_process:
            # Check rate limit before starting bulk process
            usage_stats = image_manager.get_daily_usage_stats()
            if usage_stats['remaining_calls'] <= 0:
                return jsonify({
                    'success': False,
                    'message': f'Daily API rate limit reached ({usage_stats["daily_limit"]} calls). Please try again tomorrow.'
                }), 429
            
            # Adjust limit based on remaining calls
            effective_limit = min(limit, usage_stats['remaining_calls'])
            
            # Process multiple articles
            def bulk_process_background():
                try:
                    processed = image_manager.bulk_process_articles_for_images(effective_limit)
                    print(f"✅ Bulk image processing completed: {processed} articles processed")
                except Exception as e:
                    print(f"❌ Error in bulk image processing: {e}")
            
            # Run in background thread
            thread = threading.Thread(target=bulk_process_background)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'status': 'started',
                'message': f'Bulk image processing started for up to {effective_limit} articles (Rate limit: {usage_stats["remaining_calls"]} calls remaining)'
            })
        
        else:
            return jsonify({'error': 'Please specify article_id or set bulk_process=true'}), 400
            
    except Exception as e:
        logger.error(f"Error in process_article_images: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/article_images/<int:article_id>')
def get_article_images(article_id):
    """Get all images for a specific article"""
    try:
        images = image_manager.get_article_images(article_id)
        return jsonify({'images': images})
        
    except Exception as e:
        logger.error(f"Error getting article images: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/image-stats')
def get_image_statistics():
    """Get image statistics for dashboard"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Get total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # Get articles with images
        cursor.execute("""
            SELECT COUNT(DISTINCT article_id) 
            FROM article_images 
            WHERE is_deleted = 0
        """)
        articles_with_images = cursor.fetchone()[0]
        
        # Calculate articles without images
        articles_without_images = total_articles - articles_with_images
        
        # Get total images
        cursor.execute("SELECT COUNT(*) FROM article_images WHERE is_deleted = 0")
        total_images = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_articles': total_articles,
                'articles_with_images': articles_with_images,
                'articles_without_images': articles_without_images,
                'total_images': total_images
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting image statistics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/image-usage-stats')
def get_image_usage_statistics():
    """Get daily API usage statistics for image processing"""
    try:
        usage_stats = image_manager.get_daily_usage_stats()
        
        return jsonify({
            'success': True,
            'usage': usage_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting image usage statistics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/scraper-protection-stats')
@admin_required
def get_scraper_protection_stats():
    """Get anti-scraping protection statistics - Admin only"""
    try:
        stats = scraper_protection.get_rate_limit_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting scraper protection stats: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/unblock-ip', methods=['POST'])
@admin_required
def unblock_ip():
    """Unblock an IP address - Admin only"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400
        
        success = scraper_protection.unblock_ip(ip_address)
        
        return jsonify({
            'success': success,
            'message': f'IP {ip_address} {"unblocked" if success else "not found or already unblocked"}'
        })
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/bookmark/<int:article_id>', methods=['POST'])
def bookmark_article(article_id):
    """Bookmark an article"""
    bookmark_name = request.json.get('name', f'Bookmark {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO bookmarks (article_id, bookmark_name) VALUES (?, ?)', 
                  (article_id, bookmark_name))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Article bookmarked successfully'})

@app.route('/bookmarks')
def bookmarks():
    """View bookmarked articles"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.id, b.bookmark_name, b.created_at, a.id, a.title, a.source_type, a.category
        FROM bookmarks b
        JOIN articles a ON b.article_id = a.id
        ORDER BY b.created_at DESC
    ''')
    
    bookmarks_data = cursor.fetchall()
    conn.close()
    
    return render_template('bookmarks.html', bookmarks=bookmarks_data)

@app.route('/settings')
def settings():
    """Settings page for configuring WiseNews"""
    return render_template('settings.html')

@app.route('/export')
def export_data():
    """Export articles as JSON"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, content, source_type, source_name, 
               date_added, keywords, category
        FROM articles 
        ORDER BY date_added DESC
    ''')
    
    articles_data = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    articles_list = []
    for article in articles_data:
        articles_list.append({
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'source_type': article[3],
            'source_name': article[4],
            'date_added': article[5],
            'keywords': article[6],
            'category': article[7]
        })
    
    # Save to file
    export_filename = f'news_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    export_path = os.path.join('downloads', export_filename)
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(articles_list, f, indent=2, ensure_ascii=False)
    
    return send_file(export_path, as_attachment=True)

# PWA API endpoints
@app.route('/api/sync')
@require_api_key
def api_sync():
    """API endpoint for background sync - Requires API key"""
    try:
        # Trigger news aggregation
        from news_aggregator import aggregate_news
        threading.Thread(target=aggregate_news, daemon=True).start()
        return jsonify({'status': 'success', 'message': 'Sync started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/articles')
@require_api_key
@anti_scraper_protection
def api_articles():
    """API endpoint for getting articles - Requires API key with anti-scraping protection"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    cursor.execute('''
        SELECT id, title, content, source_type, source_name, 
               date_added, keywords, category, read_status
        FROM articles 
        WHERE (source_type != 'live_event' OR 
               (source_type = 'live_event' AND 
                CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                (SELECT id FROM live_events WHERE status = 'completed')))
        ORDER BY date_added DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    articles_data = cursor.fetchall()
    conn.close()
    
    articles_list = []
    for article in articles_data:
        articles_list.append({
            'id': article[0],
            'title': article[1],
            'content': article[2][:500] + '...' if len(article[2]) > 500 else article[2],
            'source_type': article[3],
            'source_name': article[4],
            'date_added': article[5],
            'keywords': article[6],
            'category': article[7],
            'read_status': article[8]
        })
    
    return jsonify({'articles': articles_list})

@app.route('/api/duplicate-stats')
@require_api_key
def duplicate_stats():
    """API endpoint for duplicate detection statistics - Requires API key"""
    """API endpoint for duplicate detection statistics"""
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Count total articles
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    # Count articles by source
    cursor.execute('SELECT source_type, COUNT(*) FROM articles GROUP BY source_type')
    sources = dict(cursor.fetchall())
    
    # Count recent articles (last 24 hours)
    cursor.execute('SELECT COUNT(*) FROM articles WHERE date_added >= datetime("now", "-1 day")')
    recent_articles = cursor.fetchone()[0]
    
    # Check for potential duplicates (similar titles)
    cursor.execute('''
        SELECT title, COUNT(*) as count 
        FROM articles 
        GROUP BY SUBSTR(title, 1, 30) 
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    ''')
    potential_duplicates = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_articles': total_articles,
        'sources': sources,
        'recent_articles': recent_articles,
        'potential_duplicates': potential_duplicates,
        'duplicate_prevention': 'Active'
    })

@app.route('/api/news-count')
@require_api_key
def api_news_count():
    """API endpoint for getting total news count - Requires API key"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Count total articles
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        # Count recent articles (last 24 hours)
        cursor.execute('SELECT COUNT(*) FROM articles WHERE date_added >= datetime("now", "-1 day")')
        recent_articles = cursor.fetchone()[0]
        
        # Count by category
        cursor.execute('SELECT category, COUNT(*) FROM articles GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5')
        top_categories = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'total_articles': total_articles,
            'recent_articles': recent_articles,
            'top_categories': top_categories,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# =============================================================================
# USER AUTHENTICATION ROUTES
# =============================================================================

@app.route('/register')
def register_form():
    """User registration form"""
    return render_template('register.html')

@app.route('/register', methods=['POST'])
@anti_scraping_protection
def register_user():
    """Process user registration"""
    try:
        # Get form data
        user_data = {
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password'),
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'country': request.form.get('country', '').strip(),
            'date_of_birth': request.form.get('date_of_birth'),
            'phone_number': request.form.get('phone_number', '').strip(),
            'terms_accepted': request.form.get('terms_accepted') == 'on',
            'privacy_policy_accepted': request.form.get('privacy_policy_accepted') == 'on',
            'age_verification': request.form.get('age_verification') == 'on',
            'gdpr_consent': request.form.get('gdpr_consent') == 'on',
            'marketing_consent': request.form.get('marketing_consent') == 'on',
            'analytics_consent': request.form.get('analytics_consent') == 'on',
            'data_processing_consent': request.form.get('data_processing_consent') == 'on',
            'data_retention_agreed': request.form.get('data_retention_agreed') == 'on'
        }
        
        # Get user IP for logging
        ip_address = get_user_ip()
        
        # Register user
        success, message, user_id = user_manager.register_user(user_data, ip_address)
        
        if success:
            # Automatically start free trial for new users
            trial_success, trial_message = subscription_manager.start_free_trial(user_id)
            if trial_success:
                flash('Registration successful! Your 7-day free trial has started. Please check your email to verify your account.', 'success')
            else:
                flash('Registration successful! Please check your email to verify your account.', 'success')
                
            return redirect(url_for('login'))
        else:
            flash(f'Registration failed: {message}', 'danger')
            return render_template('register.html', form_data=user_data)
            
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'danger')
        return render_template('register.html')

@app.route('/login')
def login_form():
    """User login form"""
    next_url = request.args.get('next')
    return render_template('login.html', next_url=next_url)

@app.route('/login', methods=['POST'])
@anti_scraping_protection
def login_user():
    """Process user login"""
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        next_url = request.form.get('next')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html', next_url=next_url)
        
        # Get user info for logging
        ip_address = get_user_ip()
        user_agent = get_user_agent()
        
        # Authenticate user
        success, message, user_id = user_manager.authenticate_user(email, password, ip_address)
        
        if success:
            # Create session
            session_token = user_manager.create_session(user_id, ip_address, user_agent)
            session['session_token'] = session_token
            session['user_id'] = user_id
            
            # Set session expiry
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False
                app.permanent_session_lifetime = timedelta(hours=2)
            
            flash('Login successful! Welcome to WiseNews.', 'success')
            
            # Redirect to next URL or dashboard
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            else:
                return redirect(url_for('dashboard'))
        else:
            flash(f'Login failed: {message}', 'danger')
            return render_template('login.html', email=email, next_url=next_url)
            
    except Exception as e:
        flash(f'Login error: {str(e)}', 'danger')
        return render_template('login.html')

@app.route('/logout')
def logout_user():
    """User logout"""
    session_token = session.get('session_token')
    
    if session_token:
        user_manager.logout_user(session_token)
    
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def user_profile():
    """User profile page"""
    user = get_current_user()
    
    # Get full user data - using 'id' key instead of 'user_id'
    user_data = user_manager.get_user_data(user['id'])
    
    return render_template('profile.html', user_data=user_data)

@app.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        user = get_current_user()
        
        # Get updated data
        updated_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'country': request.form.get('country', '').strip(),
            'phone_number': request.form.get('phone_number', '').strip(),
        }
        
        # Update user in database
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET first_name = ?, last_name = ?, country = ?, phone_number = ?
            WHERE id = ?
        ''', (updated_data['first_name'], updated_data['last_name'], 
              updated_data['country'], updated_data['phone_number'], user['user_id']))
        
        conn.commit()
        conn.close()
        
        # Log data processing
        user_manager.log_data_processing(
            user['user_id'],
            'profile_update',
            'personal_data',
            'consent',
            'profile_management',
            get_user_ip()
        )
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))
        
    except Exception as e:
        flash(f'Profile update failed: {str(e)}', 'danger')
        return redirect(url_for('user_profile'))

@app.route('/privacy-settings')
@login_required
def privacy_settings():
    """Privacy and consent settings"""
    user = get_current_user()
    
    # Get current consent settings
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT gdpr_consent, marketing_consent, analytics_consent, data_processing_consent
        FROM users WHERE id = ?
    ''', (user['user_id'],))
    
    consent_data = cursor.fetchone()
    conn.close()
    
    consent_settings = {
        'gdpr_consent': consent_data[0] if consent_data else False,
        'marketing_consent': consent_data[1] if consent_data else False,
        'analytics_consent': consent_data[2] if consent_data else False,
        'data_processing_consent': consent_data[3] if consent_data else False,
    }
    
    return render_template('privacy_settings.html', consent_settings=consent_settings)

@app.route('/privacy-settings', methods=['POST'])
@login_required
def update_privacy_settings():
    """Update privacy and consent settings"""
    try:
        user = get_current_user()
        
        # Get consent updates
        consent_updates = {
            'marketing_consent': request.form.get('marketing_consent') == 'on',
            'analytics_consent': request.form.get('analytics_consent') == 'on',
            'data_processing_consent': request.form.get('data_processing_consent') == 'on',
        }
        
        # Update in database
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET marketing_consent = ?, analytics_consent = ?, data_processing_consent = ?
            WHERE id = ?
        ''', (consent_updates['marketing_consent'], consent_updates['analytics_consent'],
              consent_updates['data_processing_consent'], user['user_id']))
        
        conn.commit()
        conn.close()
        
        # Log consent changes
        user_manager.log_data_processing(
            user['user_id'],
            'consent_update',
            'consent_data',
            'consent',
            'gdpr_compliance',
            get_user_ip()
        )
        
        flash('Privacy settings updated successfully!', 'success')
        return redirect(url_for('privacy_settings'))
        
    except Exception as e:
        flash(f'Privacy settings update failed: {str(e)}', 'danger')
        return redirect(url_for('privacy_settings'))

@app.route('/delete-account')
@login_required
def request_account_deletion():
    """Request account deletion (GDPR right to be forgotten)"""
    return render_template('delete_account.html')

@app.route('/delete-account', methods=['POST'])
@login_required
def process_account_deletion():
    """Process account deletion request"""
    user = get_current_user()
    confirmation = request.form.get('confirmation')
    
    if confirmation != 'DELETE':
        flash('Please type "DELETE" to confirm account deletion.', 'danger')
        return render_template('delete_account.html')
    
    try:
        # Mark account for deletion (30-day grace period)
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        deletion_date = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            UPDATE users SET account_deletion_requested = ?
            WHERE id = ?
        ''', (deletion_date, user['user_id']))
        
        conn.commit()
        conn.close()
        
        # Log data processing
        user_manager.log_data_processing(
            user['user_id'],
            'deletion_request',
            'personal_data',
            'consent',
            'gdpr_right_to_be_forgotten',
            get_user_ip()
        )
        
        # Logout user
        session_token = session.get('session_token')
        if session_token:
            user_manager.logout_user(session_token)
        session.clear()
        
        flash('Account deletion requested. Your account will be deleted in 30 days. You can cancel this by logging in again.', 'warning')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Account deletion request failed: {str(e)}', 'danger')
        return render_template('delete_account.html')

# =============================================================================
# API KEY MANAGEMENT ROUTES
# =============================================================================

@app.route('/api/apply')
def api_application_form():
    """API key application form"""
    return render_template('api_apply.html')

@app.route('/api/apply', methods=['POST'])
@anti_scraping_protection
def submit_api_application():
    """Submit API key application"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        organization = data.get('organization', '')
        key_name = data.get('key_name')
        purpose = data.get('purpose', '')
        
        if not email or not key_name:
            return jsonify({
                'error': 'Missing required fields',
                'required': ['email', 'key_name']
            }), 400
        
        # Generate API key
        result = api_manager.generate_api_key(email, organization, key_name)
        
        return jsonify({
            'success': True,
            'api_key': result['api_key'],
            'status': result['status'],
            'message': result['message'],
            'next_steps': 'Your application has been submitted. You will receive email confirmation when approved.'
        })
        
    except Exception as e:
        return jsonify({'error': 'Application failed', 'message': str(e)}), 500

@app.route('/api/docs')
def api_documentation():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/admin/api-keys')
@browser_only
def admin_api_keys():
    """Admin panel for managing API keys"""
    # Simple admin authentication (you should implement proper auth)
    admin_key = request.args.get('admin_key')
    if admin_key != 'wisenews_admin_2025':  # Change this to a secure key
        return render_template('admin_login.html')
    
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Get pending applications
    cursor.execute('''
        SELECT id, key_name, api_key, email, organization, created_at, status
        FROM api_keys 
        ORDER BY created_at DESC
    ''')
    applications = cursor.fetchall()
    
    # Get usage stats
    cursor.execute('''
        SELECT ak.key_name, ak.email, ak.usage_count, ak.last_used, ak.rate_limit
        FROM api_keys ak
        WHERE ak.status = 'active'
        ORDER BY ak.usage_count DESC
    ''')
    usage_stats = cursor.fetchall()
    
    # Get recent API usage
    cursor.execute('''
        SELECT au.api_key, au.endpoint, au.ip_address, au.timestamp, ak.key_name
        FROM api_usage au
        JOIN api_keys ak ON au.api_key = ak.api_key
        ORDER BY au.timestamp DESC
        LIMIT 50
    ''')
    recent_usage = cursor.fetchall()
    
    # Get blocked access
    cursor.execute('''
        SELECT ip_address, user_agent, reason, blocked_at, auto_block
        FROM blocked_access
        ORDER BY blocked_at DESC
        LIMIT 50
    ''')
    blocked_access = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_api_keys.html',
                         applications=applications,
                         usage_stats=usage_stats,
                         recent_usage=recent_usage,
                         blocked_access=blocked_access)

@app.route('/admin/approve-key', methods=['POST'])
@browser_only
def approve_api_key():
    """Approve pending API key"""
    admin_key = request.form.get('admin_key')
    if admin_key != 'wisenews_admin_2025':
        return jsonify({'error': 'Unauthorized'}), 401
    
    api_key = request.form.get('api_key')
    rate_limit = int(request.form.get('rate_limit', 100))
    
    success = api_manager.approve_api_key(api_key, rate_limit)
    
    if success:
        return jsonify({'success': True, 'message': 'API key approved'})
    else:
        return jsonify({'error': 'Failed to approve API key'}), 400

@app.route('/admin/block-access', methods=['POST'])
@browser_only  
def block_access():
    """Block IP or User Agent"""
    admin_key = request.form.get('admin_key')
    if admin_key != 'wisenews_admin_2025':
        return jsonify({'error': 'Unauthorized'}), 401
    
    ip_address = request.form.get('ip_address')
    user_agent = request.form.get('user_agent')
    reason = request.form.get('reason', 'Manually blocked by admin')
    
    api_manager.auto_block_scraper(ip_address, user_agent, reason)
    
    return jsonify({'success': True, 'message': 'Access blocked successfully'})

# =============================================================================
# PROTECTED CONTENT ROUTES  
# =============================================================================

def start_auto_refresh():
    """Start automatic news refresh in background"""
    if not AUTO_REFRESH_ENABLED:
        return
        
    def refresh_news():
        while True:
            try:
                print(f"[{datetime.now()}] WiseNews: Starting automatic news refresh...")
                from integrated_aggregator import aggregate_news
                aggregate_news()
                load_articles_to_db()
                print(f"[{datetime.now()}] WiseNews: News refresh completed")
            except Exception as e:
                print(f"[{datetime.now()}] WiseNews: Error in auto-refresh: {e}")
            
            # Wait for next refresh
            time.sleep(REFRESH_INTERVAL_MINUTES * 60)
    
    # Start in background thread
    refresh_thread = threading.Thread(target=refresh_news, daemon=True)
    refresh_thread.start()
    print(f"WiseNews: Auto-refresh started (every {REFRESH_INTERVAL_MINUTES} minutes)")

# ============================================================================
# SUBSCRIPTION MANAGEMENT ROUTES
# ============================================================================

@app.route('/subscription-plans')
@login_required
def subscription_plans():
    """Display available subscription plans"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    try:
        # Get all plans
        plans = subscription_manager.get_all_plans()
        
        # Get current subscription with error handling
        current_subscription = subscription_manager.get_user_subscription(user_id)
        
        # Get daily usage with error handling
        daily_usage = subscription_manager.get_daily_usage(user_id)
        
        # Ensure daily_usage has all required fields
        if not daily_usage:
            daily_usage = {
                'articles_viewed': 0,
                'searches_performed': 0,
                'bookmarks_created': 0,
                'api_requests': 0
            }
        
        # Ensure all required fields exist
        daily_usage.setdefault('articles_viewed', 0)
        daily_usage.setdefault('searches_performed', 0)
        daily_usage.setdefault('bookmarks_created', 0)
        daily_usage.setdefault('api_requests', 0)
        
        return render_template('subscription_plans.html', 
                             plans=plans or [], 
                             current_subscription=current_subscription,
                             daily_usage=daily_usage)
                             
    except Exception as e:
        print(f"Error in subscription_plans route: {e}")
        flash('Unable to load subscription plans. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/my-subscription')
@login_required
def my_subscription():
    """Display user's current subscription details"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    try:
        # Get current subscription with error handling
        subscription = subscription_manager.get_user_subscription(user_id)
        
        if not subscription:
            flash('No active subscription found.', 'info')
            return redirect(url_for('subscription_plans'))
        
        # Get daily usage with error handling
        daily_usage = subscription_manager.get_daily_usage(user_id)
        
        # Ensure daily_usage has all required fields
        if not daily_usage:
            daily_usage = {
                'articles_viewed': 0,
                'searches_performed': 0,
                'bookmarks_created': 0,
                'api_requests': 0
            }
        
        # Ensure all required fields exist
        daily_usage.setdefault('articles_viewed', 0)
        daily_usage.setdefault('searches_performed', 0)
        daily_usage.setdefault('bookmarks_created', 0)
        daily_usage.setdefault('api_requests', 0)
        
        return render_template('my_subscription.html', 
                             subscription=subscription,
                             daily_usage=daily_usage)
                             
    except Exception as e:
        print(f"Error in my_subscription route: {e}")
        flash('Unable to load subscription details. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/start-trial', methods=['POST'])
@login_required
def start_trial():
    """Start free trial for user"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    success, message = subscription_manager.start_free_trial(user_id)
    
    if success:
        flash('Your 7-day free trial has started! Enjoy full access to WiseNews.', 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('subscription_plans'))

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Handle subscription signup"""
    try:
        user = get_current_user()
        user_id = user.get('id') if user else None
        
        if not user_id:
            flash('Unable to identify user session.', 'error')
            return redirect(url_for('login'))
        
        plan_id = request.form.get('plan_id')
        billing_cycle = request.form.get('billing_cycle', 'monthly')
        
        if not plan_id:
            flash('Please select a valid plan.', 'error')
            return redirect(url_for('subscription_plans'))
        
        # Get plan details
        plans = subscription_manager.get_all_plans()
        selected_plan = next((p for p in plans if p['id'] == int(plan_id)), None)
        
        if not selected_plan:
            flash('Invalid plan selected.', 'error')
            return redirect(url_for('subscription_plans'))
        
        # For now, we'll just create a mock subscription
        # In a real implementation, you'd integrate with Stripe or another payment processor
        
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        try:
            # Check if user already has an active subscription
            cursor.execute('''
                SELECT id FROM user_subscriptions 
                WHERE user_id = ? AND status IN ('active', 'trial')
            ''', (user_id,))
            
            existing_subscription = cursor.fetchone()
            if existing_subscription:
                flash('You already have an active subscription.', 'info')
                return redirect(url_for('my_subscription'))
            
            # Calculate subscription dates
            start_date = datetime.now()
            if billing_cycle == 'yearly':
                end_date = start_date + timedelta(days=365)
                amount = selected_plan.get('price_yearly', 0) or 0
            else:
                end_date = start_date + timedelta(days=30)
                amount = selected_plan.get('price_monthly', 0) or 0
            
            # Create subscription record
            cursor.execute('''
                INSERT INTO user_subscriptions 
                (user_id, plan_id, status, subscription_start_date, subscription_end_date, payment_method)
                VALUES (?, ?, 'active', ?, ?, 'mock_payment')
            ''', (user_id, plan_id, start_date, end_date))
            
            subscription_id = cursor.lastrowid
            
            # Create payment record
            cursor.execute('''
                INSERT INTO payment_history 
                (user_id, subscription_id, amount, status, payment_method)
                VALUES (?, ?, ?, 'success', 'mock_payment')
            ''', (user_id, subscription_id, amount))
            
            conn.commit()
            
            flash(f'Successfully subscribed to {selected_plan["display_name"]}! Welcome to WiseNews Premium.', 'success')
            return redirect(url_for('my_subscription'))
            
        except Exception as db_error:
            conn.rollback()
            logger.error(f"Database error in subscription: {db_error}")
            flash('Database error occurred. Please try again.', 'error')
            return redirect(url_for('subscription_plans'))
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        flash('An error occurred while processing your subscription. Please try again.', 'error')
        return redirect(url_for('subscription_plans'))

@app.route('/cancel-subscription', methods=['POST', 'GET'])
@login_required
def cancel_subscription():
    """Cancel user's subscription"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update subscription status
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_subscriptions 
            SET status = 'cancelled', auto_renew = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        flash('Your subscription has been cancelled. You can continue using WiseNews until your current billing period ends.', 'info')
        return redirect(url_for('my_subscription'))
    
    # GET request - show confirmation page
    subscription = subscription_manager.get_user_subscription(user_id)
    return render_template('cancel_subscription.html', subscription=subscription)

@app.route('/billing-history')
@login_required
def billing_history():
    """Display user's billing history"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ph.amount, ph.currency, ph.payment_method, ph.status, ph.payment_date,
               sp.display_name as plan_name
        FROM payment_history ph
        JOIN user_subscriptions us ON ph.subscription_id = us.id
        JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE ph.user_id = ?
        ORDER BY ph.payment_date DESC
    ''', (user_id,))
    
    payments = cursor.fetchall()
    conn.close()
    
    return render_template('billing_history.html', payments=payments)

# API Key management routes (with alias for backward compatibility)
@app.route('/api-keys')
@login_required
def api_keys_alias():
    """Alias for API management route"""
    return redirect(url_for('api_management'))

@app.route('/api-management')
@login_required
def api_management():
    """Manage API keys for users with API access"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    subscription = subscription_manager.get_user_subscription(user_id)
    if not subscription or not subscription['api_access']:
        flash('API access is not available in your current plan.', 'error')
        return redirect(url_for('subscription_plans'))
    
    # Get daily usage data
    daily_usage = subscription_manager.get_daily_usage(user_id)
    
    # Ensure daily_usage has all required fields
    if not daily_usage:
        daily_usage = {
            'articles_viewed': 0,
            'searches_performed': 0,
            'bookmarks_created': 0,
            'api_requests': 0
        }
    
    # Ensure all required fields exist
    daily_usage.setdefault('articles_viewed', 0)
    daily_usage.setdefault('searches_performed', 0)
    daily_usage.setdefault('bookmarks_created', 0)
    daily_usage.setdefault('api_requests', 0)
    
    # Add daily_usage to subscription for template
    subscription['daily_usage'] = daily_usage
    
    # Get user's API keys
    user_data = user_manager.get_user_by_id(user_id)
    api_keys = api_manager.get_user_keys(user_data['email'])
    
    return render_template('api_management.html', api_keys=api_keys, subscription=subscription)

@app.route('/export-user-data')
@login_required
def export_user_data():
    """Export user's data (for users with export feature)"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    subscription = subscription_manager.get_user_subscription(user_id)
    if not subscription or not subscription['export_data']:
        flash('Data export is not available in your current plan.', 'error')
        return redirect(url_for('subscription_plans'))
    
    # Implementation for data export would go here
    flash('Data export feature will be available soon.', 'info')
    return redirect(url_for('my_subscription'))

# Usage tracking middleware
@app.before_request
def track_usage():
    """Track user usage for subscription limits"""
    session_token = session.get('session_token')
    if session_token and request.endpoint:
        # Validate session and get user ID
        is_valid, user_data = user_manager.validate_session(session_token)
        if is_valid and user_data:
            user_id = user_data.get('id')
            
            # Track different types of usage based on endpoint
            if request.endpoint == 'view_article':
                # Check if user can view more articles
                can_use, message = subscription_manager.check_usage_limit(user_id, 'articles_viewed')
                if not can_use:
                    flash(f'Daily article limit reached: {message}', 'warning')
                    return redirect(url_for('subscription_plans'))
                
                # Track article view (only if within limits)
                subscription_manager.track_usage(user_id, 'articles_viewed')
        
        elif request.endpoint == 'search' and request.method == 'GET' and request.args.get('q'):
            # Check search limits only when actually performing a search
            can_use, message = subscription_manager.check_usage_limit(user_id, 'searches_performed')
            if not can_use:
                flash(f'Daily search limit reached: {message}', 'warning')
                return redirect(url_for('subscription_plans'))
            
            # Track search (only if within limits)
            subscription_manager.track_usage(user_id, 'searches_performed')

# ============================================================================
# NOTIFICATION MANAGEMENT ROUTES
# ============================================================================

@app.route('/notification-preferences', methods=['GET', 'POST'])
@login_required
def notification_preferences():
    """Manage user notification preferences"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    # Check if user has access to real-time notifications
    has_access, access_message = has_real_time_notifications_access(user_id)
    
    if request.method == 'POST':
        # Get form data
        preferences = {
            'email_notifications': 'email_notifications' in request.form,
            'push_notifications': 'push_notifications' in request.form,
            'notification_frequency': request.form.get('notification_frequency', 'daily'),
            'time_preference': request.form.get('time_preference', '09:00'),
            'timezone': request.form.get('timezone', 'UTC'),
            'categories': [cat.strip() for cat in request.form.get('categories', '').split(',') if cat.strip()],
            'keywords': [kw.strip() for kw in request.form.get('keywords', '').split(',') if kw.strip()],
            'sources': request.form.getlist('sources')
        }
        
        # Restrict instant notifications to premium users only
        if preferences['notification_frequency'] == 'instant' and not has_access:
            flash(f'Instant notifications are only available for Premium subscribers. {access_message}', 'warning')
            preferences['notification_frequency'] = 'daily'  # Fallback to daily
        
        success = notification_manager.update_user_preferences(user_id, preferences)
        
        if success:
            flash('Notification preferences updated successfully!', 'success')
        else:
            flash('Error updating preferences. Please try again.', 'error')
        
        return redirect(url_for('notification_preferences'))
    
    # GET request - show preferences form
    preferences = notification_manager.get_user_preferences(user_id) or {
        'email_notifications': True,
        'push_notifications': False,
        'notification_frequency': 'daily',
        'time_preference': '09:00',
        'timezone': 'UTC',
        'categories': [],
        'keywords': [],
        'sources': []
    }
    
    # Force non-premium users to daily/weekly notifications
    if not has_access and preferences.get('notification_frequency') == 'instant':
        preferences['notification_frequency'] = 'daily'
    
    # Get available options
    available_categories = notification_manager.get_available_categories()
    available_sources = notification_manager.get_available_sources()
    
    # Get notification history
    notification_history = notification_manager.get_notification_history(user_id, 10)
    
    # Get current subscription for display
    current_subscription = subscription_manager.get_user_subscription(user_id)
    
    return render_template('notification_preferences.html',
                         preferences=preferences,
                         available_categories=available_categories,
                         available_sources=available_sources,
                         notification_history=notification_history,
                         has_real_time_access=has_access,
                         access_message=access_message,
                         current_subscription=current_subscription)

@app.route('/subscribe-push', methods=['POST'])
@login_required
def subscribe_push():
    """Subscribe to push notifications"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        return jsonify({'error': 'Unable to identify user session'}), 401
    
    subscription_data = request.json
    
    success = notification_manager.subscribe_to_push(user_id, subscription_data)
    
    if success:
        return jsonify({'success': True, 'message': 'Push notifications enabled'})
    else:
        return jsonify({'success': False, 'message': 'Failed to enable push notifications'}), 500

@app.route('/test-notification', methods=['POST'])
@login_required
def test_notification():
    """Send a test notification to the user - Premium feature for instant testing"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        return jsonify({'error': 'Unable to identify user session'}), 401
    
    # Check if user has access to real-time notifications for instant testing
    has_access, access_message = has_real_time_notifications_access(user_id)
    
    if not has_access:
        flash(f'Test notifications are available for Premium subscribers only. {access_message}', 'warning')
        return redirect(url_for('notification_preferences'))
    
    # Create a mock article for testing
    test_article = {
        'id': 0,
        'title': 'Welcome to WiseNews Real-Time Notifications!',
        'content': 'This is a test notification to verify your Premium subscription real-time settings are working correctly.',
        'category': 'Technology',
        'source_name': 'WiseNews Premium'
    }
    
    notification_manager.queue_notification(user_id, test_article, 'both')
    
    flash('Premium test notification queued! You should receive it based on your frequency settings.', 'success')
    return redirect(url_for('notification_preferences'))

@app.route('/notification-history')
@login_required
def notification_history():
    """View notification history"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    history = notification_manager.get_notification_history(user_id, 50)
    
    return render_template('notification_history.html', notifications=history)

@app.route('/unsubscribe')
def unsubscribe():
    """Unsubscribe from all notifications"""
    user_id = request.args.get('user_id')
    if user_id:
        preferences = {
            'email_notifications': False,
            'push_notifications': False
        }
        notification_manager.update_user_preferences(int(user_id), preferences)
        flash('You have been unsubscribed from all notifications.', 'info')
    
    return redirect(url_for('index'))

# Hook into article loading to trigger notifications
def trigger_article_notifications(article_data):
    """Trigger notifications for new articles based on user preferences and subscription level"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Get all users with notification preferences and their subscription info
        cursor.execute('''
            SELECT np.user_id, np.notification_frequency, sp.real_time_notifications, us.status
            FROM notification_preferences np
            JOIN user_subscriptions us ON np.user_id = us.user_id
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE (np.email_notifications = TRUE OR np.push_notifications = TRUE)
            AND us.status IN ('active', 'trial')
        ''')
        
        user_notifications = cursor.fetchall()
        conn.close()
        
        # Queue notifications based on subscription level
        for user_id, frequency, has_real_time, status in user_notifications:
            # Check if user wants instant notifications
            if frequency == 'instant':
                # Only Premium users get instant notifications
                if has_real_time:
                    notification_manager.queue_notification(user_id, article_data)
                    logger.info(f"Instant notification queued for Premium user {user_id}")
                else:
                    # For non-premium users requesting instant, queue as daily instead
                    logger.info(f"User {user_id} requested instant but doesn't have Premium - using daily instead")
                    # Update their preference to daily automatically
                    try:
                        current_prefs = notification_manager.get_user_preferences(user_id)
                        if current_prefs:
                            current_prefs['notification_frequency'] = 'daily'
                            notification_manager.update_user_preferences(user_id, current_prefs)
                    except Exception as pref_error:
                        logger.error(f"Failed to update user {user_id} preferences: {pref_error}")
            else:
                # Daily and weekly notifications are available for all plans
                notification_manager.queue_notification(user_id, article_data)
                logger.info(f"Scheduled notification queued for user {user_id} ({frequency})")
            
    except Exception as e:
        logger.error(f"Error triggering notifications: {e}")

# Live Events Routes
@app.route('/live-events')
@login_required
def live_events():
    """Enhanced live events dashboard with WebSocket support"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    try:
        # Use enhanced live events if available
        if enhanced_live_events:
            events_data = enhanced_live_events.get_active_events()
            user_subscriptions = enhanced_live_events.get_user_subscriptions(user_id)
            websocket_enabled = True
            
            # Get enhanced event data with recent updates
            for event in events_data:
                event['recent_updates'] = enhanced_live_events.get_recent_updates(event['id'], limit=5)
                event['last_updated'] = enhanced_live_events.get_last_update_time(event['id'])
                event['is_subscribed'] = event['id'] in user_subscriptions
            
        else:
            # Fallback to basic functionality
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            try:
                # Get only currently active live events (status = 'live' and recent)
                cursor.execute('''
                    SELECT id, event_name, description, category, status, event_type, created_at, last_updated,
                           (SELECT COUNT(*) FROM live_event_updates WHERE event_id = live_events.id) as update_count
                    FROM live_events 
                    WHERE status = 'live' 
                    AND created_at >= datetime('now', '-2 hours')
                    ORDER BY last_updated DESC, created_at DESC
                ''')
                
                active_events = cursor.fetchall()
                
                # Get user's event subscriptions
                cursor.execute('''
                    SELECT event_id FROM user_event_subscriptions 
                    WHERE user_id = ? AND is_active = TRUE
                ''', (user_id,))
                
                user_subscriptions = [row[0] for row in cursor.fetchall()]
                
                # Format events data for template
                events_data = []
                for event in active_events:
                    events_data.append({
                        'id': event[0],
                        'title': event[1],  # event_name mapped to title
                        'description': event[2],
                        'category': event[3],
                        'status': event[4],
                        'event_type': event[5],
                        'created_at': event[6],
                        'updated_at': event[7],
                        'update_count': event[8],
                        'is_subscribed': event[0] in user_subscriptions,
                        'recent_updates': [],
                        'last_updated': event[7]
                    })
                
                websocket_enabled = False
                
            finally:
                conn.close()
        
        # Get categories that have active events
        active_categories = list(set([event['category'] for event in events_data]))
        
    except Exception as e:
        print(f"Error fetching live events: {e}")
        events_data = []
        active_categories = []
        user_subscriptions = []
        websocket_enabled = False
    
    return render_template('live_events.html', 
                         events=events_data, 
                         categories=active_categories,
                         subscriptions=user_subscriptions,
                         has_active_events=len(events_data) > 0,
                         websocket_enabled=websocket_enabled,
                         enhanced_features=ENHANCED_LIVE_EVENTS_AVAILABLE)

@app.route('/live-events/<int:event_id>')
@login_required
def live_event_detail(event_id):
    """Live event detail page with real-time updates"""
    from live_events_manager import live_events_manager
    
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        flash('Unable to identify user session.', 'error')
        return redirect(url_for('login'))
    
    # Get event details
    events = live_events_manager.get_live_events()
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('live_events'))
    
    # Get event updates
    updates = live_events_manager.get_event_updates(event_id)
    
    # Check if user is subscribed
    conn = sqlite3.connect('news_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT notification_types FROM user_event_subscriptions 
        WHERE user_id = ? AND event_id = ? AND is_active = TRUE
    ''', (user_id, event_id))
    
    subscription = cursor.fetchone()
    is_subscribed = subscription is not None
    notification_types = json.loads(subscription[0]) if subscription else []
    conn.close()
    
    return render_template('live_event_detail.html', 
                         event=event, 
                         updates=updates,
                         is_subscribed=is_subscribed,
                         notification_types=notification_types)

@app.route('/api/live-events/active-count')
@login_required
def get_active_events_count():
    """Get count of currently active live events"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Count currently active events (within last 2 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM live_events 
            WHERE status = 'live' 
            AND created_at >= datetime('now', '-2 hours')
        ''')
        
        active_count = cursor.fetchone()[0]
        
        # Get breakdown by category
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM live_events 
            WHERE status = 'live' 
            AND created_at >= datetime('now', '-2 hours')
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        category_breakdown = dict(cursor.fetchall())
        
        # Get some sample active events
        cursor.execute('''
            SELECT event_name, category, created_at
            FROM live_events 
            WHERE status = 'live' 
            AND created_at >= datetime('now', '-2 hours')
            ORDER BY last_updated DESC
            LIMIT 5
        ''')
        
        sample_events = [{'name': row[0], 'category': row[1], 'created': row[2]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'active_count': active_count,
            'categories': category_breakdown,
            'sample_events': sample_events,
            'has_events': active_count > 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'active_count': 0,
            'has_events': False
        }), 500

@app.route('/api/live-events/search')
@login_required
def search_live_events():
    """Search for live events"""
    from live_events_manager import live_events_manager
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({'events': []})
    
    events = live_events_manager.search_events(query)
    return jsonify({'events': events})

@app.route('/api/live-events/<int:event_id>/subscribe', methods=['POST'])
@login_required
def subscribe_to_event(event_id):
    """Subscribe to live event updates"""
    from live_events_manager import live_events_manager
    
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Unable to identify user session'}), 401
    
    # Check if user has premium access for real-time notifications
    if not has_real_time_notifications_access(user_id):
        return jsonify({
            'success': False, 
            'message': 'Premium subscription required for live event notifications'
        }), 403
    
    data = request.get_json()
    notification_types = data.get('notification_types', ['all'])
    
    success = live_events_manager.subscribe_user_to_event(
        user_id, 
        event_id, 
        notification_types
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Subscribed to event updates'})
    else:
        return jsonify({'success': False, 'message': 'Failed to subscribe to event'}), 500

@app.route('/api/live-events/<int:event_id>/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_from_event(event_id):
    """Unsubscribe from live event updates"""
    user = get_current_user()
    user_id = user.get('id') if user else None
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Unable to identify user session'}), 401
    
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_event_subscriptions 
            SET is_active = FALSE 
            WHERE user_id = ? AND event_id = ?
        ''', (user_id, event_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Unsubscribed from event updates'})
        
    except Exception as e:
        logger.error(f"Error unsubscribing from event: {e}")
        return jsonify({'success': False, 'message': 'Failed to unsubscribe from event'}), 500

@app.route('/api/live-events/<int:event_id>/updates')
@login_required
def get_event_updates_api(event_id):
    """Get latest updates for an event (for real-time refresh)"""
    from live_events_manager import live_events_manager
    
    since = request.args.get('since')  # Timestamp to get updates after
    limit = int(request.args.get('limit', 20))
    
    updates = live_events_manager.get_event_updates(event_id, limit)
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            updates = [u for u in updates if datetime.fromisoformat(u['timestamp']) > since_dt]
        except ValueError:
            pass  # Invalid timestamp, return all updates
    
    return jsonify({'updates': updates})

@app.route('/test-enhanced-notification', methods=['POST'])
@login_required
def test_enhanced_notification():
    """Test the enhanced notification system - Admin only for demo purposes"""
    try:
        user = get_current_user()
        user_id = user.get('id') if user else None
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Unable to identify user session'}), 401
        
        from notification_manager import NotificationManager
        notification_manager = NotificationManager()
        
        # Sample article data with rich metadata
        sample_article = {
            'id': 99999,  # Test ID
            'title': 'Breaking: Major AI Breakthrough Revolutionizes Medical Diagnosis',
            'content': 'Scientists at leading research institutions have announced a groundbreaking artificial intelligence system that can diagnose complex medical conditions with 99.5% accuracy. This revolutionary technology promises to transform healthcare delivery and improve patient outcomes worldwide. The system combines advanced machine learning algorithms with vast medical databases to provide instant, accurate diagnoses that previously required extensive testing and expert consultation. Early trials show remarkable success rates across multiple medical specialties including oncology, cardiology, and neurology.',
            'category': 'Technology',
            'source_name': 'Medical Research Weekly',
            'keywords': ['ai', 'artificial intelligence', 'medical', 'breakthrough', 'diagnosis', 'healthcare', 'technology'],
            'url': 'https://example.com/ai-medical-breakthrough'
        }
        
        # Queue enhanced notification for current user
        notification_manager.queue_notification(user_id, sample_article, 'both')
        
        return jsonify({
            'success': True, 
            'message': 'Enhanced notification queued! Check your notification preferences and history to see the detailed content.'
        })
        
    except Exception as e:
        logger.error(f"Error testing enhanced notification: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/live-events/categories')
@login_required
def get_event_categories():
    """Get available event categories"""
    from live_events_manager import live_events_manager
    
    categories = live_events_manager.get_active_categories()
    return jsonify({'categories': categories})

# ============================================================================
# ENHANCED LIVE EVENTS API ENDPOINTS (WebSocket Support)
# ============================================================================

@app.route('/api/live-events/performance')
@login_required
def live_events_performance():
    """Get live events performance metrics (Enhanced features)"""
    if not enhanced_live_events:
        return jsonify({'error': 'Enhanced live events not available'}), 503
    
    try:
        metrics = enhanced_live_events.get_performance_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics,
            'websocket_enabled': True,
            'enhanced_features': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-events/websocket-status')
@login_required
def websocket_status():
    """Check WebSocket connection status and capabilities"""
    return jsonify({
        'websocket_available': ENHANCED_LIVE_EVENTS_AVAILABLE,
        'enhanced_features_enabled': enhanced_live_events is not None,
        'socketio_initialized': socketio is not None,
        'connection_info': {
            'ping_timeout': 60,
            'ping_interval': 25,
            'transport_methods': ['websocket', 'polling']
        }
    })

@app.route('/api/live-events/<int:event_id>/priority')
@login_required
def get_event_priority(event_id):
    """Get event priority and update settings (Enhanced features)"""
    if not enhanced_live_events:
        return jsonify({'error': 'Enhanced live events not available'}), 503
    
    try:
        priority_info = enhanced_live_events.get_event_priority(event_id)
        return jsonify({
            'success': True,
            'event_id': event_id,
            'priority_info': priority_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-events/connection-stats')
@login_required
def connection_statistics():
    """Get real-time connection statistics (Enhanced features)"""
    if not enhanced_live_events:
        return jsonify({'error': 'Enhanced live events not available'}), 503
    
    try:
        stats = enhanced_live_events.get_connection_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# QUICK UPDATES API ENDPOINTS (Ultra-Fast Performance)
# ============================================================================

@app.route('/api/quick-updates/performance')
def quick_updates_performance():
    """Get quick updates performance metrics"""
    if quick_updates:
        metrics = quick_updates.get_performance_metrics()
        return jsonify(metrics)
    return jsonify({'error': 'Quick updates not available'}), 503

@app.route('/api/quick-updates/trigger', methods=['POST'])
@login_required
def trigger_quick_update():
    """Manually trigger a quick update (for testing)"""
    if not quick_updates:
        return jsonify({'error': 'Quick updates not available'}), 503
    
    data = request.get_json()
    update_type = data.get('type', 'test')
    update_data = data.get('data', {})
    priority = data.get('priority', 'normal')
    
    try:
        quick_updates.add_quick_update(update_type, update_data, priority)
        return jsonify({'success': True, 'message': 'Update triggered'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-updates/cached-articles')
def get_cached_articles():
    """Get articles from cache for faster loading"""
    if not quick_updates:
        return jsonify({'error': 'Quick updates not available'}), 503
    
    category = request.args.get('category')
    source = request.args.get('source')
    limit = request.args.get('limit', 20, type=int)
    
    try:
        articles = quick_updates.get_cached_articles(category, source, limit)
        return jsonify({'articles': articles, 'cached': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-updates/subscribe', methods=['POST'])
@login_required
def subscribe_to_quick_updates():
    """Subscribe to specific update types"""
    if not quick_updates:
        return jsonify({'error': 'Quick updates not available'}), 503
    
    data = request.get_json()
    update_types = data.get('update_types', [])
    session_id = request.sid if hasattr(request, 'sid') else 'web_user'
    
    try:
        quick_updates.subscribe_to_updates(session_id, update_types)
        return jsonify({'success': True, 'subscribed_to': update_types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/loading')
def loading_screen():
    """Show loading screen with optional redirect"""
    message = request.args.get('message', 'Loading...')
    redirect_url = request.args.get('redirect_url', '')
    redirect_delay = request.args.get('delay', 3000, type=int)
    
    return render_template('loading.html', 
                         message=message,
                         redirect_url=redirect_url,
                         redirect_delay=redirect_delay)


@app.route('/quick-updates')
def quick_updates():
    """Display quick updates and notifications"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Get recent notifications/updates
        cursor.execute('''
            SELECT id, title, content, category, source_name, date_added, priority, notification_type
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
                'source_name': row[4],
                'date_added': row[5],
                'priority': row[6],
                'notification_type': row[7]
            })
        
        conn.close()
        
        return render_template('quick_updates.html', 
                             notifications=notifications,
                             title='Quick Updates & Notifications')
    
    except Exception as e:
        print(f"Error loading quick updates: {e}")
        return render_template('error.html', error="Unable to load quick updates")

@app.route('/mark-notification-read/<int:notification_id>')
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('quick_updates'))
    
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return redirect(url_for('quick_updates'))

@app.route('/admin/archive-live-events', methods=['POST'])
@admin_required
def manual_archive_live_events():
    """Manually trigger live events archiving (admin only)"""
    try:
        # Mark events as completed
        completed_count = live_events_archiver.mark_events_completed_by_time()
        
        # Archive completed events
        archived_count = live_events_archiver.archive_completed_events()
        
        flash(f'Successfully marked {completed_count} events as completed and archived {archived_count} events', 'success')
        
    except Exception as e:
        flash(f'Error during archiving: {e}', 'error')
    
    return redirect(url_for('live_events'))


def start_live_events_archiver():
    """Start the live events archiver background task"""
    def archiver_loop():
        while True:
            try:
                # Mark events as completed based on end time
                live_events_archiver.mark_events_completed_by_time()
                
                # Archive completed events to articles/notifications
                archived_count = live_events_archiver.archive_completed_events()
                if archived_count > 0:
                    logger.info(f"Archived {archived_count} completed live events")
                
                # Clean up old events (weekly)
                import time
                current_hour = datetime.now().hour
                if current_hour == 2:  # Run cleanup at 2 AM
                    cleaned_count = live_events_archiver.cleanup_old_live_events()
                    if cleaned_count > 0:
                        logger.info(f"Cleaned up {cleaned_count} old live events")
                
                # Wait 5 minutes before next check
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in live events archiver: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    # Start archiver in background thread
    thread = threading.Thread(target=archiver_loop, daemon=True)
    thread.start()


@app.route('/articles-fast')
def articles_fast():
    """Optimized articles page with previews and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Show fewer articles per page
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Get only essential fields + preview
    cursor.execute("""
        SELECT id, title, 
               SUBSTR(content, 1, 200) as preview,
               source_name, date_added, category
        FROM articles 
        ORDER BY date_added DESC 
        LIMIT ? OFFSET ?
    """, (per_page, (page-1) * per_page))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'preview': row[2] + '...' if len(row[2]) == 200 else row[2],
            'source_name': row[3],
            'date_added': row[4],
            'category': row[5]
        })
    
    # Get total count for pagination
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('articles_fast.html', 
                         articles=articles,
                         page=page,
                         per_page=per_page,
                         total=total,
                         has_next=page * per_page < total,
                         has_prev=page > 1)


if __name__ == '__main__':
    init_db()
    # load_articles_to_db()  # DISABLED FOR DEBUGGING - CAUSES 500 ERRORS
    print("⚠️ ARTICLE IMPORT DISABLED FOR DEBUGGING")
    
    # Start notification processor
    try:
        start_notification_processor()
        logger.info("Notification processor started successfully")
    except Exception as e:
        logger.error(f"Failed to start notification processor: {e}")
    
    # Start automatic news refresh
    start_auto_refresh()
    
    # Start integrated aggregation system - TEMPORARILY DISABLED FOR DEBUGGING
    # try:
    #     from integrated_aggregator import start_integrated_aggregation
    #     start_integrated_aggregation()
    #     logger.info("Integrated data aggregation started successfully")
    # except Exception as e:
    #     logger.error(f"Failed to start integrated aggregation: {e}")
    print("⚠️ INTEGRATED AGGREGATION DISABLED FOR DEBUGGING")
    
    # Start live events tracking
    try:
        live_events_manager.start_live_tracking()
        logger.info("Live events tracking started successfully")
    except Exception as e:
        logger.error(f"Failed to start live events tracking: {e}")
    
    # Start live events archiver
    try:
        start_live_events_archiver()
        logger.info("Live events archiver started successfully")
    except Exception as e:
        logger.error(f"Failed to start live events archiver: {e}")
    
    # Enhanced live events already initialized with background processors
    if enhanced_live_events:
        logger.info("Enhanced live events system ready with WebSocket support")
    
    # BROWSER PROTECTION: Clear any browser blocks and ensure browsers are never blocked
    try:
        from api_security import api_manager
        api_manager.clear_browser_blocks()
        logger.info("Browser protection initialized - all browser blocks cleared")
    except Exception as e:
        logger.error(f"Failed to initialize browser protection: {e}")
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # SECURITY: Never run with debug=True in production!
    # Debug mode exposes sensitive system information to users
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # Start the application
    if ENHANCED_LIVE_EVENTS_AVAILABLE and socketio:
        print("Starting WiseNews with enhanced WebSocket live events support")
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=port, 
                    debug=debug_mode,
                    allow_unsafe_werkzeug=True)
    else:
        print("Starting WiseNews with basic functionality")
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
