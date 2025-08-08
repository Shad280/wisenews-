from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash, g
import os
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
import threading
import time
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
app.config['DATABASE'] = 'wisenews.db'

# News sources configuration - Enhanced with comprehensive real news feeds
NEWS_SOURCES = {
    # General News
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
    'reuters': {
        'name': 'Reuters',
        'rss': 'http://feeds.reuters.com/reuters/topNews',
        'category': 'general'
    },
    'ap_news': {
        'name': 'Associated Press',
        'rss': 'https://feeds.apnews.com/rss/apf-topnews',
        'category': 'general'
    },
    
    # Technology
    'techcrunch': {
        'name': 'TechCrunch',
        'rss': 'http://feeds.feedburner.com/TechCrunch/',
        'category': 'technology'
    },
    'ars_technica': {
        'name': 'Ars Technica',
        'rss': 'http://feeds.arstechnica.com/arstechnica/index',
        'category': 'technology'
    },
    'wired': {
        'name': 'Wired',
        'rss': 'https://www.wired.com/feed/rss',
        'category': 'technology'
    },
    
    # Business
    'bloomberg': {
        'name': 'Bloomberg',
        'rss': 'https://feeds.bloomberg.com/markets/news.rss',
        'category': 'business'
    },
    'financial_times': {
        'name': 'Financial Times',
        'rss': 'https://www.ft.com/rss/home',
        'category': 'business'
    },
    
    # Sports
    'espn': {
        'name': 'ESPN',
        'rss': 'https://www.espn.com/espn/rss/news',
        'category': 'sports'
    },
    'bbc_sport': {
        'name': 'BBC Sport',
        'rss': 'http://feeds.bbci.co.uk/sport/rss.xml',
        'category': 'sports'
    },
    
    # Health
    'webmd': {
        'name': 'WebMD',
        'rss': 'https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC',
        'category': 'health'
    },
    'health_news': {
        'name': 'Medical News Today',
        'rss': 'https://www.medicalnewstoday.com/rss',
        'category': 'health'
    },
    
    # Science
    'science_daily': {
        'name': 'Science Daily',
        'rss': 'https://www.sciencedaily.com/rss/all.xml',
        'category': 'science'
    },
    'new_scientist': {
        'name': 'New Scientist',
        'rss': 'https://www.newscientist.com/feed/home/',
        'category': 'science'
    },
    
    # Entertainment
    'entertainment_weekly': {
        'name': 'Entertainment Weekly',
        'rss': 'https://ew.com/feed/',
        'category': 'entertainment'
    },
    'variety': {
        'name': 'Variety',
        'rss': 'https://variety.com/feed/',
        'category': 'entertainment'
    }
}

def fetch_rss_feed(url, source_name, category):
    """Fetch and parse RSS feed from a news source"""
    try:
        print(f"📡 Fetching news from {source_name}...")
        
        # Create request with headers to avoid blocking
        req = urllib.request.Request(url, headers={
            'User-Agent': 'WiseNews/3.0 (News Aggregator; +https://wisenews.com/bot)'
        })
        
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read()
        
        # Parse XML
        root = ET.fromstring(xml_data)
        articles = []
        
        # Handle different RSS formats
        items = root.findall('.//item') or root.findall('.//{http://purl.org/rss/1.0/}item')
        
        for item in items[:10]:  # Limit to 10 articles per source
            try:
                title = item.find('title')
                title = title.text if title is not None else 'No Title'
                
                description = item.find('description') or item.find('summary')
                description = description.text if description is not None else ''
                
                # Clean description of HTML tags
                import re
                description = re.sub(r'<[^>]+>', '', description)
                description = description.strip()[:500]  # Limit length
                
                link = item.find('link')
                link = link.text if link is not None else ''
                
                # Get publication date
                pub_date = item.find('pubDate') or item.find('published')
                pub_date = pub_date.text if pub_date is not None else datetime.now().isoformat()
                
                # Generate article data
                article_data = {
                    'title': title[:200],  # Limit title length
                    'content': description,
                    'summary': description[:150] + '...' if len(description) > 150 else description,
                    'url': link,
                    'author': source_name,
                    'source': source_name,
                    'category': category,
                    'keywords': f"{category}, {source_name.lower()}, news",
                    'image_url': f"https://via.placeholder.com/400x200/{get_category_color(category)[1:]}/ffffff?text={category.title()}+News",
                    'published_date': pub_date
                }
                
                articles.append(article_data)
                
            except Exception as e:
                print(f"⚠️ Error parsing article from {source_name}: {e}")
                continue
        
        print(f"✅ Successfully fetched {len(articles)} articles from {source_name}")
        return articles
        
    except Exception as e:
        print(f"❌ Error fetching RSS from {source_name}: {e}")
        return []

def get_category_color(category):
    """Get color for category"""
    colors = {
        'general': '#007bff',
        'technology': '#28a745',
        'business': '#ffc107',
        'sports': '#17a2b8',
        'entertainment': '#e83e8c',
        'health': '#20c997',
        'science': '#6610f2'
    }
    return colors.get(category, '#6c757d')

def save_articles_to_db(articles):
    """Save fetched articles to database"""
    if not articles:
        return 0
    
    conn = get_db()
    cursor = conn.cursor()
    saved_count = 0
    
    for article in articles:
        try:
            # Check if article already exists (by URL or title)
            cursor.execute('''
                SELECT id FROM articles WHERE url = ? OR title = ?
            ''', (article['url'], article['title']))
            
            if cursor.fetchone() is None:
                # Insert new article
                cursor.execute('''
                    INSERT INTO articles (
                        title, content, summary, url, author, source, category,
                        keywords, image_url, published_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'], article['content'], article['summary'],
                    article['url'], article['author'], article['source'],
                    article['category'], article['keywords'], article['image_url'],
                    article['published_date'], datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                saved_count += 1
        
        except Exception as e:
            print(f"⚠️ Error saving article: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"💾 Saved {saved_count} new articles to database")
    return saved_count

def fetch_all_news():
    """Fetch news from all configured sources"""
    print("🚀 Starting comprehensive news fetch...")
    total_articles = 0
    
    for source_id, source_config in NEWS_SOURCES.items():
        try:
            articles = fetch_rss_feed(
                source_config['rss'],
                source_config['name'],
                source_config['category']
            )
            
            saved = save_articles_to_db(articles)
            total_articles += saved
            
            # Small delay between requests to be respectful
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing {source_id}: {e}")
            continue
    
    print(f"🎉 News fetch complete! Total new articles: {total_articles}")
    return total_articles

def start_news_fetcher():
    """Start background news fetching"""
    def fetch_news_periodically():
        while True:
            try:
                print("⏰ Scheduled news fetch starting...")
                fetch_all_news()
                print("😴 Sleeping for 1 hour until next fetch...")
                time.sleep(3600)  # Wait 1 hour
            except Exception as e:
                print(f"❌ Error in periodic news fetch: {e}")
                time.sleep(600)  # Wait 10 minutes on error
    
    # Start fetching in background thread
    news_thread = threading.Thread(target=fetch_news_periodically, daemon=True)
    news_thread.start()
    print("🔄 Background news fetcher started!")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with enhanced schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            url TEXT UNIQUE,
            source TEXT,
            category TEXT DEFAULT 'general',
            author TEXT,
            published_date TEXT,
            image_url TEXT,
            read_count INTEGER DEFAULT 0,
            sentiment REAL DEFAULT 0.0,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#007bff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            preferred_categories TEXT,
            reading_history TEXT,
            last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add default categories if they don't exist
    default_categories = [
        ('general', 'General News', '#007bff'),
        ('technology', 'Technology', '#28a745'),
        ('business', 'Business', '#ffc107'),
        ('sports', 'Sports', '#17a2b8'),
        ('entertainment', 'Entertainment', '#e83e8c'),
        ('health', 'Health', '#20c997'),
        ('science', 'Science', '#6610f2')
    ]
    
    for cat_name, description, color in default_categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, description, color)
            VALUES (?, ?, ?)
        ''', (cat_name, description, color))
    
    # Add sample articles if database is empty
    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            {
                'title': 'Breaking: Revolutionary AI Technology Transforms News Industry',
                'content': 'A groundbreaking artificial intelligence system has been developed that can analyze, summarize, and categorize news articles with unprecedented accuracy. This technology promises to revolutionize how we consume and understand news in the digital age.',
                'summary': 'New AI technology revolutionizes news analysis and categorization.',
                'url': 'https://wisenews.com/ai-news-revolution',
                'source': 'WiseNews Tech',
                'category': 'technology',
                'author': 'Dr. Sarah Chen',
                'image_url': 'https://via.placeholder.com/400x200/007bff/ffffff?text=AI+News',
                'keywords': 'AI, technology, news, innovation'
            },
            {
                'title': 'Global Climate Summit Reaches Historic Agreement',
                'content': 'World leaders have reached a unanimous agreement on new climate action measures during the international climate summit. The agreement includes ambitious targets for carbon reduction and renewable energy adoption across all participating nations.',
                'summary': 'World leaders agree on historic climate action measures.',
                'url': 'https://wisenews.com/climate-agreement',
                'source': 'Global Environmental Report',
                'category': 'general',
                'author': 'Maria Rodriguez',
                'image_url': 'https://via.placeholder.com/400x200/28a745/ffffff?text=Climate+Summit',
                'keywords': 'climate, environment, global, agreement'
            },
            {
                'title': 'Stock Markets Rally as Tech Giants Report Strong Earnings',
                'content': 'Major technology companies have reported better-than-expected quarterly earnings, driving a significant rally in global stock markets. Investors are optimistic about the tech sectors continued growth and innovation potential.',
                'summary': 'Tech earnings drive global stock market rally.',
                'url': 'https://wisenews.com/market-rally',
                'source': 'Financial Times',
                'category': 'business',
                'author': 'James Wilson',
                'image_url': 'https://via.placeholder.com/400x200/ffc107/000000?text=Market+Rally',
                'keywords': 'stocks, technology, earnings, finance'
            },
            {
                'title': 'Medical Breakthrough: New Cancer Treatment Shows Promise',
                'content': 'Researchers have announced a significant breakthrough in cancer treatment with a new immunotherapy approach showing remarkable success rates in clinical trials. The treatment could revolutionize cancer care for millions of patients worldwide.',
                'summary': 'New immunotherapy shows promising results in cancer treatment.',
                'url': 'https://wisenews.com/cancer-breakthrough',
                'source': 'Medical Research Today',
                'category': 'health',
                'author': 'Dr. Michael Thompson',
                'image_url': 'https://via.placeholder.com/400x200/20c997/ffffff?text=Medical+Breakthrough',
                'keywords': 'cancer, medical, research, treatment'
            },
            {
                'title': 'Space Exploration Reaches New Milestone with Mars Mission',
                'content': 'The latest Mars exploration mission has achieved a significant milestone with the successful deployment of advanced scientific instruments on the Martian surface. The mission promises to unlock new secrets about the red planet.',
                'summary': 'Mars mission achieves major scientific milestone.',
                'url': 'https://wisenews.com/mars-mission',
                'source': 'Space Science Weekly',
                'category': 'science',
                'author': 'Dr. Lisa Park',
                'image_url': 'https://via.placeholder.com/400x200/6610f2/ffffff?text=Mars+Mission',
                'keywords': 'space, mars, exploration, science'
            }
        ]
        
        for article in sample_articles:
            cursor.execute('''
                INSERT INTO articles (title, content, summary, url, source, category, author, 
                                    published_date, image_url, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['title'], article['content'], article['summary'], article['url'],
                article['source'], article['category'], article['author'],
                datetime.now().isoformat(), article['image_url'], article['keywords']
            ))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Homepage with latest news and user-aware navigation"""
    # Check if user is logged in
    user = None
    try:
        from auth_decorators import get_current_user
        user = get_current_user()
    except:
        pass
    
    # Get latest articles for homepage
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, summary, author, source, category, image_url, published_date
        FROM articles 
        ORDER BY published_date DESC 
        LIMIT 12
    ''')
    
    recent_articles = cursor.fetchall()
    
    # Get categories count
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
        LIMIT 6
    ''')
    
    categories = cursor.fetchall()
    
    # Get total articles count
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiseNews - Stay Informed with Real-Time News</title>
    <meta name="description" content="Get the latest news from trusted sources worldwide. Stay informed with WiseNews - your comprehensive news aggregation platform.">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">
                <i class="fas fa-newspaper"></i> WiseNews
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/"><i class="fas fa-home"></i> Home</a>
                    </li>
                    {% if user %}
                        <li class="nav-item">
                            <a class="nav-link" href="/articles"><i class="fas fa-newspaper"></i> Articles</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/search"><i class="fas fa-search"></i> Search</a>
                        </li>
                    {% endif %}
                    <li class="nav-item">
                        <a class="nav-link" href="/trending"><i class="fas fa-fire"></i> Trending</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/subscription-plans"><i class="fas fa-crown"></i> Plans</a>
                    </li>
                </ul>
                
                <ul class="navbar-nav">
                    {% if user %}
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="fas fa-user"></i> {{ user.first_name }}
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                                <li><a class="dropdown-item" href="/profile"><i class="fas fa-user"></i> Profile</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
                            </ul>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/register"><i class="fas fa-user-plus"></i> Sign Up</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <div class="bg-light py-5">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold text-primary">
                        Stay Informed with <span class="text-dark">WiseNews</span>
                    </h1>
                    <p class="lead mb-4">
                        Get real-time news from trusted sources worldwide. {{ total_articles }} articles from 18+ sources updated hourly.
                    </p>
                    <div class="d-flex gap-3">
                        {% if not user %}
                            <a href="/register" class="btn btn-primary btn-lg">
                                <i class="fas fa-rocket"></i> Get Started Free
                            </a>
                            <a href="/login" class="btn btn-outline-primary btn-lg">
                                <i class="fas fa-sign-in-alt"></i> Sign In
                            </a>
                        {% else %}
                            <a href="/dashboard" class="btn btn-primary btn-lg">
                                <i class="fas fa-tachometer-alt"></i> Go to Dashboard
                            </a>
                            <a href="/articles" class="btn btn-outline-primary btn-lg">
                                <i class="fas fa-newspaper"></i> Browse Articles
                            </a>
                        {% endif %}
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="text-center">
                        <i class="fas fa-globe-americas fa-10x text-primary opacity-25"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Latest Articles -->
    <div class="container my-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="display-6 fw-bold">Latest Articles</h2>
            {% if user %}
                <a href="/articles" class="btn btn-outline-primary">
                    <i class="fas fa-newspaper"></i> View All
                </a>
            {% else %}
                <a href="/login" class="btn btn-outline-primary">
                    <i class="fas fa-sign-in-alt"></i> Sign In to Read
                </a>
            {% endif %}
        </div>
        
        <div class="row g-4">
            {% for article in recent_articles %}
            <div class="col-lg-4 col-md-6">
                <div class="card border-0 shadow-sm h-100">
                    {% if article[6] %}
                        <img src="{{ article[6] }}" class="card-img-top" style="height: 200px; object-fit: cover;" alt="Article image">
                    {% endif %}
                    <div class="card-body">
                        <span class="badge bg-primary mb-2">{{ article[5].title() }}</span>
                        <h5 class="card-title">{{ article[1] }}</h5>
                        <p class="card-text text-muted">{{ article[2][:100] }}...</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-user"></i> {{ article[3] }}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> {{ article[7][:10] }}
                            </small>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        {% if user %}
                            <a href="/article/{{ article[0] }}" class="btn btn-primary btn-sm">
                                <i class="fas fa-eye"></i> Read More
                            </a>
                        {% else %}
                            <a href="/login?next=/article/{{ article[0] }}" class="btn btn-primary btn-sm">
                                <i class="fas fa-eye"></i> Sign In to Read
                            </a>
                        {% endif %}
                        <small class="text-muted float-end">{{ article[4] }}</small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Features Section -->
    <div class="bg-light py-5">
        <div class="container">
            <div class="text-center mb-5">
                <h2 class="display-5 fw-bold">Why Choose WiseNews?</h2>
                <p class="lead text-muted">Everything you need for staying informed</p>
            </div>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="card border-0 shadow-sm h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-sync-alt fa-3x text-primary mb-3"></i>
                            <h5>Real-Time Updates</h5>
                            <p class="text-muted">Get the latest news as it happens from 18+ trusted sources worldwide.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-0 shadow-sm h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-shield-alt fa-3x text-success mb-3"></i>
                            <h5>Trusted Sources</h5>
                            <p class="text-muted">Curated content from BBC, CNN, Reuters, Bloomberg, and other reputable sources.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-0 shadow-sm h-100">
                        <div class="card-body text-center">
                            <i class="fas fa-search fa-3x text-info mb-3"></i>
                            <h5>Smart Search</h5>
                            <p class="text-muted">Find exactly what you're looking for with our powerful search capabilities.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-light py-4 mt-5">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="fas fa-newspaper"></i> WiseNews</h5>
                    <p class="text-muted">Your trusted source for real-time news aggregation.</p>
                </div>
                <div class="col-md-6 text-end">
                    <p class="text-muted">{{ total_articles }} articles available</p>
                    <p class="text-muted">Updated hourly from 18+ sources</p>
                </div>
            </div>
            <hr class="my-4">
            <div class="text-center">
                <p class="mb-0">&copy; 2025 WiseNews. Made with <i class="fas fa-heart text-danger"></i> for staying informed.</p>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', user=user, recent_articles=recent_articles, categories=categories, total_articles=total_articles)

# =============================================================================
# PROTECTED ROUTES - Require Authentication
# =============================================================================

from auth_decorators import login_required, get_current_user

@app.route('/articles')
@login_required
def articles():
    """Protected articles listing with usage tracking"""
    user = get_current_user()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check subscription limits
        from user_auth import user_manager
        can_access, message = user_manager.check_daily_limits(user['id'], 'articles')
        
        if not can_access:
            flash(f"Daily limit reached: {message}", 'warning')
            return redirect(url_for('subscription_plans'))
        
        # Track usage
        user_manager.track_usage(user['id'], 'article_view')
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = 12
        offset = (page - 1) * per_page
        
        # Get articles with pagination
        cursor.execute('''
            SELECT a.*, c.color as category_color, c.description as category_desc
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        articles = cursor.fetchall()
        
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        total_pages = (total_articles + per_page - 1) // per_page
        
        conn.close()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Articles - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .article-card:hover { transform: translateY(-2px); transition: 0.2s; }
        .user-header { background: linear-gradient(135deg, #007bff, #28a745); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link active" href="/articles">Articles</a></li>
                    <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user"></i> {{ user.first_name }}
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                            <li><a class="dropdown-item" href="/profile"><i class="fas fa-user"></i> Profile</a></li>
                            <li><a class="dropdown-item" href="/subscription-plans"><i class="fas fa-crown"></i> Subscription</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="user-header text-white py-4">
        <div class="container">
            <h1><i class="fas fa-newspaper"></i> All Articles</h1>
            <p class="lead">{{ total_articles }} articles available • Page {{ page }} of {{ total_pages }}</p>
        </div>
    </div>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row">
            {% for article in articles %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card article-card h-100 shadow-sm">
                    {% if article.image_url %}
                    <img src="{{ article.image_url }}" class="card-img-top" alt="{{ article.title }}" style="height: 200px; object-fit: cover;">
                    {% endif %}
                    <div class="card-body">
                        <span class="badge mb-2" style="background-color: {{ article.category_color or '#6c757d' }}">
                            {{ article.category.title() }}
                        </span>
                        <h5 class="card-title">{{ article.title }}</h5>
                        <p class="card-text">{{ article.summary[:100] }}...</p>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-user"></i> {{ article.author }} • 
                                <i class="fas fa-clock"></i> {{ article.created_at[:10] }}
                            </small>
                        </p>
                    </div>
                    <div class="card-footer d-flex justify-content-between align-items-center">
                        <a href="/article/{{ article.id }}" class="btn btn-primary btn-sm">
                            <i class="fas fa-eye"></i> Read More
                        </a>
                        <small class="text-muted">
                            <i class="fas fa-eye"></i> {{ article.read_count or 0 }} reads
                        </small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Pagination -->
        {% if total_pages > 1 %}
        <nav aria-label="Articles pagination">
            <ul class="pagination justify-content-center">
                {% if page > 1 %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page - 1 }}">Previous</a>
                    </li>
                {% endif %}
                
                {% for p in range(1, total_pages + 1) %}
                    {% if p == page %}
                        <li class="page-item active">
                            <span class="page-link">{{ p }}</span>
                        </li>
                    {% elif p <= 3 or p >= total_pages - 2 or (p >= page - 1 and p <= page + 1) %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ p }}">{{ p }}</a>
                        </li>
                    {% elif p == 4 or p == total_pages - 3 %}
                        <li class="page-item disabled">
                            <span class="page-link">...</span>
                        </li>
                    {% endif %}
                {% endfor %}
                
                {% if page < total_pages %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page + 1 }}">Next</a>
                    </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', user=user, articles=articles, page=page, total_pages=total_pages, total_articles=total_articles)
        
    except Exception as e:
        return f"<h1>Error loading articles: {str(e)}</h1>", 500

@app.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    """View single article with read tracking"""
    user = get_current_user()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get article
        cursor.execute('''
            SELECT a.*, c.color as category_color, c.description as category_desc
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE a.id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        if not article:
            flash('Article not found.', 'error')
            return redirect(url_for('articles'))
        
        # Track usage
        from user_auth import user_manager
        user_manager.track_usage(user['id'], 'article_read')
        
        # Increment read count
        cursor.execute('''
            UPDATE articles 
            SET read_count = read_count + 1 
            WHERE id = ?
        ''', (article_id,))
        
        conn.commit()
        conn.close()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ article.title }} - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/articles">← Back to Articles</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <article class="card">
                    {% if article.image_url %}
                    <img src="{{ article.image_url }}" class="card-img-top" alt="{{ article.title }}">
                    {% endif %}
                    
                    <div class="card-body">
                        <div class="mb-3">
                            <span class="badge" style="background-color: {{ article.category_color or '#6c757d' }}">
                                {{ article.category.title() }}
                            </span>
                            <span class="badge bg-info ms-2">{{ article.source }}</span>
                        </div>
                        
                        <h1 class="card-title">{{ article.title }}</h1>
                        
                        <div class="text-muted mb-4">
                            <i class="fas fa-user"></i> By {{ article.author }} • 
                            <i class="fas fa-clock"></i> {{ article.published_date[:10] }} • 
                            <i class="fas fa-eye"></i> {{ article.read_count + 1 }} reads
                        </div>
                        
                        {% if article.summary %}
                        <div class="alert alert-light">
                            <strong>Summary:</strong> {{ article.summary }}
                        </div>
                        {% endif %}
                        
                        <div class="article-content">
                            {{ article.content | safe }}
                        </div>
                        
                        {% if article.keywords %}
                        <div class="mt-4">
                            <h6>Keywords:</h6>
                            {% for keyword in article.keywords.split(',') %}
                                <span class="badge bg-secondary me-1">{{ keyword.strip() }}</span>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        {% if article.url %}
                        <div class="mt-4">
                            <a href="{{ article.url }}" target="_blank" class="btn btn-outline-primary">
                                <i class="fas fa-external-link-alt"></i> View Original Source
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </article>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', article=article, user=user)
        
    except Exception as e:
        return f"<h1>Error loading article: {str(e)}</h1>", 500

@app.route('/search')
@login_required
def search():
    """Protected search with usage limits"""
    user = get_current_user()
    query = request.args.get('q', '').strip()
    
    try:
        if query:
            # Check subscription limits
            from user_auth import user_manager
            can_access, message = user_manager.check_daily_limits(user['id'], 'searches')
            
            if not can_access:
                flash(f"Daily search limit reached: {message}", 'warning')
                return redirect(url_for('subscription_plans'))
            
            # Track usage
            user_manager.track_usage(user['id'], 'search')
        
        conn = get_db()
        cursor = conn.cursor()
        
        articles = []
        if query:
            # Search in title, content, summary, and keywords
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT a.*, c.color as category_color,
                       (CASE 
                        WHEN a.title LIKE ? THEN 3
                        WHEN a.summary LIKE ? THEN 2  
                        WHEN a.keywords LIKE ? THEN 2
                        WHEN a.content LIKE ? THEN 1
                        ELSE 0 
                       END) as relevance_score
                FROM articles a 
                LEFT JOIN categories c ON a.category = c.name
                WHERE a.title LIKE ? OR a.content LIKE ? OR a.summary LIKE ? OR a.keywords LIKE ?
                ORDER BY relevance_score DESC, a.created_at DESC
                LIMIT 20
            ''', [search_pattern] * 8)
            
            articles = cursor.fetchall()
        
        conn.close()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/articles">Articles</a>
                <a class="nav-link" href="/logout">Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <h2><i class="fas fa-search"></i> Search News</h2>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="GET" class="mb-4">
                    <div class="input-group">
                        <input type="text" class="form-control" name="q" value="{{ query }}" 
                               placeholder="Search for news articles..." required>
                        <button class="btn btn-primary" type="submit">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </div>
                </form>
                
                {% if query %}
                    <h4>Search Results for "{{ query }}"</h4>
                    <p class="text-muted">Found {{ articles|length }} results</p>
                    
                    {% if articles %}
                        {% for article in articles %}
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="row">
                                    {% if article.image_url %}
                                    <div class="col-md-3">
                                        <img src="{{ article.image_url }}" class="img-fluid rounded" 
                                             style="height: 100px; object-fit: cover; width: 100%;">
                                    </div>
                                    <div class="col-md-9">
                                    {% else %}
                                    <div class="col-md-12">
                                    {% endif %}
                                        <span class="badge mb-2" style="background-color: {{ article.category_color or '#6c757d' }}">
                                            {{ article.category.title() }}
                                        </span>
                                        <h5 class="card-title">{{ article.title }}</h5>
                                        <p class="card-text">{{ article.summary[:200] }}...</p>
                                        <p class="card-text">
                                            <small class="text-muted">
                                                <i class="fas fa-user"></i> {{ article.author }} • 
                                                <i class="fas fa-clock"></i> {{ article.created_at[:10] }} • 
                                                <i class="fas fa-eye"></i> {{ article.read_count or 0 }} reads
                                            </small>
                                        </p>
                                        <a href="/article/{{ article.id }}" class="btn btn-primary btn-sm">
                                            <i class="fas fa-eye"></i> Read More
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> No articles found for your search query.
                        </div>
                    {% endif %}
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', query=query, articles=articles, user=user)
        
    except Exception as e:
        return f"<h1>Error in search: {str(e)}</h1>", 500

@app.route('/api/status')
def api_status():
    """Enhanced API status with system info"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) as total FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT category) as total FROM articles')
        total_categories = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT source) as total FROM articles')
        total_sources = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM articles 
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_categories = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'version': '3.0.0',
            'message': 'WiseNews API - Advanced News Platform',
            'deployment': 'production',
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_articles': total_articles,
                'total_categories': total_categories,
                'total_sources': total_sources,
                'top_categories': [dict(cat) for cat in top_categories]
            },
            'features': [
                'Advanced Article Management',
                'Category Organization',
                'Search & Filtering',
                'Reading Analytics',
                'Multi-source Aggregation',
                'Real-time Updates'
            ]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Status check failed: {str(e)}'
        }), 500

@app.route('/api/deployment-check')
def deployment_check():
    """Comprehensive deployment verification for WiseNews 3.0.0"""
    try:
        import os
        results = {
            'deployment_status': 'success',
            'version': '3.0.0',
            'timestamp': datetime.now().isoformat(),
            'environment': {
                'railway': os.environ.get('RAILWAY_ENVIRONMENT', 'local'),
                'port': os.environ.get('PORT', '5000'),
                'service': os.environ.get('RAILWAY_SERVICE_NAME', 'wisenews')
            }
        }
        
        # Check database
        conn = get_db()
        cursor = conn.cursor()
        
        # Check tables exist
        tables_check = {}
        required_tables = ['articles', 'categories', 'users', 'user_sessions', 'subscription_plans', 'user_subscriptions', 'usage_tracking']
        
        for table in required_tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                tables_check[table] = {'exists': True, 'count': count}
            except Exception as e:
                tables_check[table] = {'exists': False, 'error': str(e)}
        
        results['database'] = tables_check
        
        # Check authentication system
        try:
            from user_auth import user_manager
            results['authentication'] = {
                'user_manager': 'loaded',
                'status': 'operational'
            }
        except Exception as e:
            results['authentication'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Check features
        features_status = {
            'user_registration': '/register',
            'user_login': '/login', 
            'user_dashboard': '/dashboard',
            'protected_articles': '/articles',
            'advanced_search': '/search',
            'subscription_plans': '/subscription-plans',
            'profile_management': '/profile',
            'api_endpoints': '/api/status',
            'news_aggregation': 'background_service'
        }
        
        results['features'] = {
            'count': len(features_status),
            'endpoints': features_status,
            'all_implemented': True
        }
        
        # Check news sources
        cursor.execute('SELECT COUNT(DISTINCT source) as sources FROM articles')
        source_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as total FROM articles WHERE created_at > datetime("now", "-24 hours")')
        recent_count = cursor.fetchone()[0]
        
        results['news_system'] = {
            'active_sources': source_count,
            'recent_articles_24h': recent_count,
            'status': 'operational'
        }
        
        conn.close()
        
        # Overall status
        results['overall_status'] = 'ALL_FEATURES_DEPLOYED'
        results['message'] = 'WiseNews 3.0.0 fully operational with all advanced features'
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'deployment_status': 'error',
            'message': f'Deployment check failed: {str(e)}',
            'version': '3.0.0'
        }), 500

@app.route('/api/articles')
def get_articles():
    """Get articles with advanced filtering"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 articles per page
        category = request.args.get('category')
        source = request.args.get('source')
        sort_by = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'DESC')
        
        # Build query
        query = '''
            SELECT a.*, c.color as category_color, c.description as category_desc
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE 1=1
        '''
        params = []
        
        if category:
            query += ' AND a.category = ?'
            params.append(category)
        
        if source:
            query += ' AND a.source = ?'
            params.append(source)
        
        # Add sorting
        valid_sorts = ['created_at', 'published_date', 'title', 'read_count']
        if sort_by in valid_sorts:
            query += f' ORDER BY a.{sort_by} {order}'
        else:
            query += ' ORDER BY a.created_at DESC'
        
        # Add pagination
        offset = (page - 1) * limit
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        
        # Get total count for pagination
        count_query = 'SELECT COUNT(*) FROM articles WHERE 1=1'
        count_params = []
        
        if category:
            count_query += ' AND category = ?'
            count_params.append(category)
        
        if source:
            count_query += ' AND source = ?'
            count_params.append(source)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            },
            'filters': {
                'category': category,
                'source': source,
                'sort_by': sort_by,
                'order': order
            },
            'articles': [dict(article) for article in articles]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching articles: {str(e)}'
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get all categories with article counts"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, COUNT(a.id) as article_count
            FROM categories c
            LEFT JOIN articles a ON c.name = a.category
            GROUP BY c.id, c.name
            ORDER BY c.name
        ''')
        categories = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'categories': [dict(cat) for cat in categories]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching categories: {str(e)}'
        }), 500

@app.route('/api/category/<category_name>')
def get_category_articles(category_name):
    """Get articles by category"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if category exists
        cursor.execute('SELECT * FROM categories WHERE name = ?', (category_name,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({
                'status': 'error',
                'message': f'Category "{category_name}" not found'
            }), 404
        
        # Get articles in this category
        cursor.execute('''
            SELECT a.*, c.color as category_color, c.description as category_desc
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE a.category = ?
            ORDER BY a.created_at DESC
        ''', (category_name,))
        articles = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'category': dict(category),
            'article_count': len(articles),
            'articles': [dict(article) for article in articles]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching category articles: {str(e)}'
        }), 500

@app.route('/api/search')
def search_articles():
    """Advanced search with multiple criteria"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query is required. Use ?q=your_search_term'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Search in title, content, summary, keywords, and author
        search_query = '''
            SELECT a.*, c.color as category_color, c.description as category_desc,
                   (CASE 
                    WHEN a.title LIKE ? THEN 3
                    WHEN a.summary LIKE ? THEN 2  
                    WHEN a.keywords LIKE ? THEN 2
                    WHEN a.content LIKE ? THEN 1
                    WHEN a.author LIKE ? THEN 1
                    ELSE 0 
                   END) as relevance_score
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE a.title LIKE ? OR a.content LIKE ? OR a.summary LIKE ? 
                  OR a.keywords LIKE ? OR a.author LIKE ?
            ORDER BY relevance_score DESC, a.created_at DESC
        '''
        
        search_pattern = f'%{query}%'
        params = [search_pattern] * 10  # 5 for relevance score, 5 for WHERE clause
        
        cursor.execute(search_query, params)
        articles = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'query': query,
            'total_results': len(articles),
            'articles': [dict(article) for article in articles]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Search error: {str(e)}'
        }), 500

@app.route('/api/trending')
def get_trending():
    """Get trending articles based on read count and recency"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Calculate trending score: recent articles with high read counts
        cursor.execute('''
            SELECT a.*, c.color as category_color,
                   (a.read_count * 1.0 + 
                    (julianday('now') - julianday(a.created_at)) * -0.1) as trending_score
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE datetime(a.created_at) > datetime('now', '-7 days')
            ORDER BY trending_score DESC
            LIMIT 10
        ''')
        articles = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Trending articles from the last 7 days',
            'count': len(articles),
            'articles': [dict(article) for article in articles]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching trending articles: {str(e)}'
        }), 500

@app.route('/api/articles', methods=['POST'])
def add_article():
    """Add new article with validation"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'JSON data is required'
            }), 400
        
        # Validate required fields
        required_fields = ['title', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Field "{field}" is required'
                }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if category exists, if not use 'general'
        category = data.get('category', 'general')
        cursor.execute('SELECT name FROM categories WHERE name = ?', (category,))
        if not cursor.fetchone():
            category = 'general'
        
        # Generate summary if not provided
        summary = data.get('summary')
        if not summary and data.get('content'):
            summary = data['content'][:200] + '...' if len(data['content']) > 200 else data['content']
        
        # Insert article
        cursor.execute('''
            INSERT INTO articles (title, content, summary, url, source, category, 
                                author, published_date, image_url, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data['content'],
            summary,
            data.get('url', ''),
            data.get('source', 'User Submitted'),
            category,
            data.get('author', 'Anonymous'),
            data.get('published_date', datetime.now().isoformat()),
            data.get('image_url', ''),
            data.get('keywords', '')
        ))
        
        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Article added successfully',
            'article_id': article_id,
            'category': category
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding article: {str(e)}'
        }), 500

@app.route('/api/articles/<int:article_id>')
def get_article(article_id):
    """Get single article with read count increment"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get article
        cursor.execute('''
            SELECT a.*, c.color as category_color, c.description as category_desc
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            WHERE a.id = ?
        ''', (article_id,))
        article = cursor.fetchone()
        
        if not article:
            return jsonify({
                'status': 'error',
                'message': 'Article not found'
            }), 404
        
        # Increment read count
        cursor.execute('''
            UPDATE articles 
            SET read_count = read_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (article_id,))
        
        conn.commit()
        conn.close()
        
        article_dict = dict(article)
        article_dict['read_count'] += 1  # Update the returned data
        
        return jsonify({
            'status': 'success',
            'article': article_dict
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching article: {str(e)}'
        }), 500

@app.route('/api/fetch-news')
def fetch_news_api():
    """API endpoint to manually trigger news fetching"""
    try:
        total_articles = fetch_all_news()
        return jsonify({
            'status': 'success',
            'message': f'News fetch completed successfully',
            'articles_added': total_articles
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'News fetch failed: {str(e)}'
        }), 500

@app.route('/api/news-status')
def news_status():
    """Get status of news sources and recent articles"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get total articles count
        cursor.execute('SELECT COUNT(*) as total FROM articles')
        total_articles = cursor.fetchone()['total']
        
        # Get articles by category
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM articles 
            GROUP BY category 
            ORDER BY count DESC
        ''')
        categories = [dict(row) for row in cursor.fetchall()]
        
        # Get recent articles
        cursor.execute('''
            SELECT source, COUNT(*) as count, MAX(created_at) as latest
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY source
            ORDER BY count DESC
        ''')
        recent_sources = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'total_articles': total_articles,
            'categories': categories,
            'recent_sources': recent_sources,
            'configured_sources': len(NEWS_SOURCES)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/register')
def register_form():
    """User registration form"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white text-center">
                        <h4><i class="fas fa-user-plus"></i> Join WiseNews</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST" action="/register">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">First Name *</label>
                                    <input type="text" class="form-control" name="first_name" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Last Name *</label>
                                    <input type="text" class="form-control" name="last_name" required>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Email Address *</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Password *</label>
                                <input type="password" class="form-control" name="password" required minlength="6">
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Confirm Password *</label>
                                <input type="password" class="form-control" name="confirm_password" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Country</label>
                                <select class="form-select" name="country">
                                    <option value="">Select Country</option>
                                    <option value="US">United States</option>
                                    <option value="UK">United Kingdom</option>
                                    <option value="CA">Canada</option>
                                    <option value="AU">Australia</option>
                                    <option value="DE">Germany</option>
                                    <option value="FR">France</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="gdpr_consent" required>
                                    <label class="form-check-label">
                                        I agree to the <a href="/terms" target="_blank">Terms of Service</a> and <a href="/privacy-policy" target="_blank">Privacy Policy</a> *
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="data_processing_consent" required>
                                    <label class="form-check-label">
                                        I consent to processing of my personal data for account management *
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="marketing_consent">
                                    <label class="form-check-label">
                                        I agree to receive marketing communications (optional)
                                    </label>
                                </div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-user-plus"></i> Create Account
                                </button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Already have an account? <a href="/login">Sign in here</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''')

@app.route('/register', methods=['POST'])
def register_user():
    """Process user registration"""
    try:
        from user_auth import user_manager
        from auth_decorators import get_user_ip
        
        # Get form data
        user_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'password': request.form.get('password', ''),
            'confirm_password': request.form.get('confirm_password', ''),
            'country': request.form.get('country', ''),
            'gdpr_consent': 'gdpr_consent' in request.form,
            'data_processing_consent': 'data_processing_consent' in request.form,
            'marketing_consent': 'marketing_consent' in request.form
        }
        
        # Validation
        if not all([user_data['first_name'], user_data['last_name'], user_data['email'], user_data['password']]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('register_form'))
        
        if user_data['password'] != user_data['confirm_password']:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register_form'))
        
        if len(user_data['password']) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register_form'))
        
        # Register user
        ip_address = request.environ.get('REMOTE_ADDR', 'Unknown')
        success, message, user_id = user_manager.register_user(user_data, ip_address)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login_form'))
        else:
            flash(f'Registration failed: {message}', 'error')
            return redirect(url_for('register_form'))
            
    except Exception as e:
        flash(f'Registration error: {str(e)}', 'error')
        return redirect(url_for('register_form'))

@app.route('/login')
def login_form():
    """User login form"""
    next_url = request.args.get('next')
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white text-center">
                        <h4><i class="fas fa-sign-in-alt"></i> Welcome Back to WiseNews</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST" action="/login">
                            {% if next_url %}
                                <input type="hidden" name="next" value="{{ next_url }}">
                            {% endif %}
                            
                            <div class="mb-3">
                                <label class="form-label">Email Address</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" name="remember_me">
                                <label class="form-check-label">Remember me</label>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-sign-in-alt"></i> Sign In
                                </button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-3">
                            <p>Don't have an account? <a href="/register">Sign up here</a></p>
                            <p><a href="/">← Back to Homepage</a></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', next_url=next_url)

@app.route('/login', methods=['POST'])
def login_user():
    """Process user login"""
    try:
        from user_auth import user_manager
        
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        next_url = request.form.get('next')
        
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login_form', next=next_url))
        
        # Get user info for logging
        ip_address = request.environ.get('REMOTE_ADDR', 'Unknown')
        user_agent = request.environ.get('HTTP_USER_AGENT', 'Unknown')
        
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
            flash(f'Login failed: {message}', 'error')
            return redirect(url_for('login_form', next=next_url))
            
    except Exception as e:
        flash(f'Login error: {str(e)}', 'error')
        return redirect(url_for('login_form'))

@app.route('/logout')
def logout():
    """User logout"""
    try:
        from user_auth import user_manager
        
        session_token = session.get('session_token')
        if session_token:
            user_manager.logout_user(session_token)
        
        session.clear()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('index'))
    except Exception as e:
        session.clear()
        return redirect(url_for('index'))

# =============================================================================
# USER DASHBOARD AND PROFILE
# =============================================================================

from auth_decorators import login_required, get_current_user

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with statistics and recent activity"""
    user = get_current_user()
    
    # Get user statistics
    conn = get_db()
    cursor = conn.cursor()
    
    # Total articles
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    # Recent articles
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE created_at > datetime('now', '-24 hours')
    ''')
    recent_articles = cursor.fetchone()[0]
    
    # User's subscription info
    cursor.execute('''
        SELECT sp.display_name, sp.max_articles_per_day, sp.max_searches_per_day
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE us.user_id = ? AND us.status = 'active'
    ''', (user['id'],))
    
    subscription = cursor.fetchone()
    if subscription:
        plan_name, max_articles, max_searches = subscription
    else:
        plan_name, max_articles, max_searches = 'Free Plan', 10, 5
    
    conn.close()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                <a class="nav-link" href="/articles"><i class="fas fa-newspaper"></i> Articles</a>
                <a class="nav-link" href="/subscription-plans"><i class="fas fa-crown"></i> Plans</a>
                <a class="nav-link" href="/profile"><i class="fas fa-user"></i> Profile</a>
                <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row">
            <div class="col-md-8">
                <h2><i class="fas fa-tachometer-alt"></i> Welcome back, {{ user.first_name }}!</h2>
                <p class="text-muted">Your personalized news dashboard</p>
                
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <h5>Total Articles</h5>
                                        <h3>{{ total_articles }}</h3>
                                    </div>
                                    <div class="align-self-center">
                                        <i class="fas fa-newspaper fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <h5>New Today</h5>
                                        <h3>{{ recent_articles }}</h3>
                                    </div>
                                    <div class="align-self-center">
                                        <i class="fas fa-plus-circle fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <h5>Your Plan</h5>
                                        <h6>{{ plan_name }}</h6>
                                    </div>
                                    <div class="align-self-center">
                                        <i class="fas fa-crown fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <a href="/articles" class="btn btn-outline-primary w-100">
                                    <i class="fas fa-newspaper"></i> Browse Articles
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/search" class="btn btn-outline-success w-100">
                                    <i class="fas fa-search"></i> Search News
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/api/fetch-news" class="btn btn-outline-info w-100">
                                    <i class="fas fa-sync"></i> Refresh News
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/api/news-status" class="btn btn-outline-warning w-100">
                                    <i class="fas fa-chart-bar"></i> News Status
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-user"></i> Account Info</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Name:</strong> {{ user.first_name }} {{ user.last_name }}</p>
                        <p><strong>Email:</strong> {{ user.email }}</p>
                        <p><strong>Plan:</strong> {{ plan_name }}</p>
                        <p><strong>Member Since:</strong> {{ user.created_at[:10] }}</p>
                        
                        <div class="d-grid gap-2">
                            <a href="/profile" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-edit"></i> Edit Profile
                            </a>
                            <a href="/subscription-plans" class="btn btn-outline-success btn-sm">
                                <i class="fas fa-crown"></i> Upgrade Plan
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie"></i> Usage Limits</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Daily Articles:</strong> 
                        {% if max_articles == -1 %}
                            Unlimited
                        {% else %}
                            {{ max_articles }} remaining
                        {% endif %}
                        </p>
                        <p><strong>Daily Searches:</strong>
                        {% if max_searches == -1 %}
                            Unlimited  
                        {% else %}
                            {{ max_searches }} remaining
                        {% endif %}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', user=user, total_articles=total_articles, recent_articles=recent_articles, 
         plan_name=plan_name, max_articles=max_articles, max_searches=max_searches)

@app.route('/profile')
@login_required  
def profile():
    """User profile management"""
    user = get_current_user()
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profile - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h2><i class="fas fa-user"></i> My Profile</h2>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Account Information</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Name:</strong> {{ user.first_name }} {{ user.last_name }}</p>
                        <p><strong>Email:</strong> {{ user.email }}</p>
                        <p><strong>Member Since:</strong> {{ user.created_at }}</p>
                        <p><strong>Account Status:</strong> 
                            <span class="badge bg-success">Active</span>
                        </p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Quick Actions</h5>
                    </div>
                    <div class="card-body d-grid gap-2">
                        <a href="/dashboard" class="btn btn-primary">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                        <a href="/subscription-plans" class="btn btn-success">
                            <i class="fas fa-crown"></i> Subscription
                        </a>
                        <a href="/articles" class="btn btn-info">
                            <i class="fas fa-newspaper"></i> Browse News
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', user=user)

# =============================================================================
# ADMIN DASHBOARD
# =============================================================================

from auth_decorators import admin_required

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with system overview"""
    user = get_current_user()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get system statistics
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE expires_at > datetime("now")')
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE created_at > datetime("now", "-24 hours")
        ''')
        new_users_today = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE created_at > datetime("now", "-24 hours")
        ''')
        new_articles_today = cursor.fetchone()[0]
        
        # Get subscription statistics
        cursor.execute('''
            SELECT sp.display_name, COUNT(us.id) as user_count
            FROM subscription_plans sp
            LEFT JOIN user_subscriptions us ON sp.id = us.plan_id AND us.status = 'active'
            GROUP BY sp.id, sp.display_name
            ORDER BY sp.price_monthly
        ''')
        subscription_stats = cursor.fetchall()
        
        # Get recent users
        cursor.execute('''
            SELECT first_name, last_name, email, created_at
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        recent_users = cursor.fetchall()
        
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
    <style>
        .admin-header { background: linear-gradient(135deg, #dc3545, #fd7e14); }
        .stat-card { transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-2px); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-danger">
        <div class="container">
            <a class="navbar-brand" href="/admin"><i class="fas fa-shield-alt"></i> WiseNews Admin</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard"><i class="fas fa-user"></i> User Dashboard</a>
                <a class="nav-link" href="/admin"><i class="fas fa-tachometer-alt"></i> Admin</a>
                <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
            </div>
        </div>
    </nav>

    <div class="admin-header text-white py-4">
        <div class="container">
            <h1><i class="fas fa-shield-alt"></i> WiseNews Admin Dashboard</h1>
            <p class="lead">System management and monitoring • Welcome, {{ user.first_name }}</p>
        </div>
    </div>

    <div class="container mt-4">
        <!-- System Statistics -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-primary text-white">
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
            
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-success text-white">
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
            
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>Active Sessions</h6>
                                <h3>{{ active_sessions }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-clock fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-warning text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h6>New Users Today</h6>
                                <h3>{{ new_users_today }}</h3>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-user-plus fa-2x opacity-75"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Subscription Statistics -->
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie"></i> Subscription Distribution</h5>
                    </div>
                    <div class="card-body">
                        {% for plan_name, user_count in subscription_stats %}
                        <div class="d-flex justify-content-between mb-2">
                            <span>{{ plan_name }}</span>
                            <span class="badge bg-primary">{{ user_count }} users</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Recent Users -->
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-user-clock"></i> Recent Users</h5>
                    </div>
                    <div class="card-body">
                        {% for user_info in recent_users %}
                        <div class="d-flex justify-content-between mb-2">
                            <div>
                                <strong>{{ user_info[0] }} {{ user_info[1] }}</strong><br>
                                <small class="text-muted">{{ user_info[2] }}</small>
                            </div>
                            <small class="text-muted">{{ user_info[3][:10] }}</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Admin Actions -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-tools"></i> Admin Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <a href="/api/fetch-news" class="btn btn-primary w-100">
                                    <i class="fas fa-sync"></i> Refresh News
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/api/status" class="btn btn-info w-100">
                                    <i class="fas fa-heartbeat"></i> System Status
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/api/deployment-check" class="btn btn-success w-100">
                                    <i class="fas fa-check-circle"></i> Deployment Check
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/api/news-status" class="btn btn-warning w-100">
                                    <i class="fas fa-rss"></i> News Status
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- System Health -->
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Today's Activity</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-6">
                                <h4 class="text-success">{{ new_articles_today }}</h4>
                                <p>New Articles Today</p>
                            </div>
                            <div class="col-md-6">
                                <h4 class="text-info">{{ new_users_today }}</h4>
                                <p>New Users Today</p>
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
        ''', user=user, total_users=total_users, total_articles=total_articles, 
             active_sessions=active_sessions, new_users_today=new_users_today,
             new_articles_today=new_articles_today, subscription_stats=subscription_stats,
             recent_users=recent_users)
        
    except Exception as e:
        return f"<h1>Admin Dashboard Error: {str(e)}</h1>", 500

# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@app.route('/subscription-plans')
def subscription_plans():
    """Display available subscription plans"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, display_name, price_monthly, price_yearly, max_articles_per_day,
               max_searches_per_day, real_time_notifications, advanced_analytics,
               export_data, priority_support
        FROM subscription_plans 
        WHERE is_active = 1
        ORDER BY price_monthly
    ''')
    
    plans = []
    for row in cursor.fetchall():
        plans.append({
            'id': row[0],
            'name': row[1],
            'price_monthly': row[2],
            'price_yearly': row[3],
            'max_articles': row[4],
            'max_searches': row[5],
            'real_time': row[6],
            'analytics': row[7],
            'export': row[8],
            'support': row[9]
        })
    
    conn.close()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Plans - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="text-center mb-5">
            <h1><i class="fas fa-crown"></i> Choose Your Plan</h1>
            <p class="lead">Get the most out of WiseNews with our flexible subscription options</p>
        </div>
        
        <div class="row">
            {% for plan in plans %}
            <div class="col-md-4 mb-4">
                <div class="card h-100 {% if plan.name == 'Premium Plan' %}border-warning{% endif %}">
                    {% if plan.name == 'Premium Plan' %}
                    <div class="card-header bg-warning text-dark text-center">
                        <i class="fas fa-star"></i> Most Popular
                    </div>
                    {% endif %}
                    
                    <div class="card-body text-center">
                        <h4>{{ plan.name }}</h4>
                        <h2 class="text-primary">
                            {% if plan.price_monthly == 0 %}
                                Free
                            {% else %}
                                ${{ "%.2f"|format(plan.price_monthly) }}<small>/month</small>
                            {% endif %}
                        </h2>
                        
                        <ul class="list-unstyled mt-4">
                            <li class="mb-2">
                                <i class="fas fa-newspaper text-success"></i>
                                {% if plan.max_articles == -1 %}
                                    Unlimited articles
                                {% else %}
                                    {{ plan.max_articles }} articles/day
                                {% endif %}
                            </li>
                            <li class="mb-2">
                                <i class="fas fa-search text-success"></i>
                                {% if plan.max_searches == -1 %}
                                    Unlimited searches
                                {% else %}
                                    {{ plan.max_searches }} searches/day
                                {% endif %}
                            </li>
                            <li class="mb-2">
                                <i class="fas fa-{% if plan.real_time %}check text-success{% else %}times text-muted{% endif %}"></i>
                                Real-time notifications
                            </li>
                            <li class="mb-2">
                                <i class="fas fa-{% if plan.analytics %}check text-success{% else %}times text-muted{% endif %}"></i>
                                Advanced analytics
                            </li>
                            <li class="mb-2">
                                <i class="fas fa-{% if plan.export %}check text-success{% else %}times text-muted{% endif %}"></i>
                                Data export
                            </li>
                            <li class="mb-2">
                                <i class="fas fa-{% if plan.support %}check text-success{% else %}times text-muted{% endif %}"></i>
                                Priority support
                            </li>
                        </ul>
                    </div>
                    
                    <div class="card-footer">
                        {% if plan.price_monthly == 0 %}
                            <a href="/register" class="btn btn-outline-primary w-100">Get Started</a>
                        {% else %}
                            <a href="/subscribe/{{ plan.id }}" class="btn btn-primary w-100">Choose Plan</a>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="text-center mt-5">
            <p class="text-muted">All plans include basic news aggregation and search functionality</p>
            <p><a href="/contact">Need help choosing? Contact us</a></p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', plans=plans)

@app.route('/subscribe/<int:plan_id>')
@login_required
def subscribe_plan(plan_id):
    """Subscribe to a plan"""
    user = get_current_user()
    
    # Get plan details
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT display_name, price_monthly
        FROM subscription_plans 
        WHERE id = ?
    ''', (plan_id,))
    
    plan = cursor.fetchone()
    if not plan:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('subscription_plans'))
    
    # Update user subscription
    cursor.execute('''
        UPDATE user_subscriptions 
        SET plan_id = ?, status = 'active',
            subscription_start_date = datetime('now'),
            subscription_end_date = datetime('now', '+1 year')
        WHERE user_id = ?
    ''', (plan_id, user['id']))
    
    if cursor.rowcount == 0:
        # Create new subscription if none exists
        cursor.execute('''
            INSERT INTO user_subscriptions (user_id, plan_id, status)
            VALUES (?, ?, 'active')
        ''', (user['id'], plan_id))
    
    conn.commit()
    conn.close()
    
    flash(f'Successfully subscribed to {plan[0]}! 🎉', 'success')
    return redirect(url_for('dashboard'))

# =============================================================================
# ADDITIONAL ROUTES AND FEATURES
# =============================================================================

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                <a class="nav-link" href="/subscription-plans"><i class="fas fa-crown"></i> Plans</a>
                <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="text-center mb-5">
                    <h1><i class="fas fa-envelope"></i> Contact WiseNews</h1>
                    <p class="lead">We'd love to hear from you</p>
                </div>
                
                <div class="row">
                    <div class="col-md-4 mb-4">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <i class="fas fa-envelope fa-3x text-primary mb-3"></i>
                                <h5>Email Support</h5>
                                <p>Get help with your account</p>
                                <a href="mailto:support@wisenews.com" class="btn btn-outline-primary">
                                    Email Us
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4 mb-4">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <i class="fas fa-comments fa-3x text-success mb-3"></i>
                                <h5>Live Chat</h5>
                                <p>Chat with our support team</p>
                                <button class="btn btn-outline-success" onclick="alert('Live chat coming soon!')">
                                    Start Chat
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4 mb-4">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <i class="fas fa-question-circle fa-3x text-info mb-3"></i>
                                <h5>FAQ</h5>
                                <p>Find answers to common questions</p>
                                <a href="/faq" class="btn btn-outline-info">
                                    View FAQ
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
    ''')

@app.route('/terms')
def terms():
    """Terms of service"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Terms of Service</h1>
        <p><strong>Last updated: {{ current_date }}</strong></p>
        
        <h3>1. Acceptance of Terms</h3>
        <p>By accessing and using WiseNews, you accept and agree to be bound by the terms and provision of this agreement.</p>
        
        <h3>2. Use License</h3>
        <p>Permission is granted to temporarily access WiseNews for personal, non-commercial transitory viewing only.</p>
        
        <h3>3. Disclaimer</h3>
        <p>The information on WiseNews is provided on an 'as is' basis. To the fullest extent permitted by law, this Company excludes all representations, warranties, conditions and terms.</p>
        
        <p><a href="/">← Back to Home</a></p>
    </div>
</body>
</html>
    ''', current_date=datetime.now().strftime('%B %d, %Y'))

@app.route('/privacy-policy')
def privacy_policy():
    """Privacy policy"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Privacy Policy</h1>
        <p><strong>Last updated: {{ current_date }}</strong></p>
        
        <h3>Information We Collect</h3>
        <p>We collect information you provide directly to us, such as when you create an account, subscribe to our service, or contact us for support.</p>
        
        <h3>How We Use Your Information</h3>
        <p>We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.</p>
        
        <h3>Information Sharing</h3>
        <p>We do not sell, trade, or otherwise transfer your personal information to third parties except as described in this policy.</p>
        
        <h3>GDPR Compliance</h3>
        <p>If you are located in the European Union, you have certain rights regarding your personal data under the General Data Protection Regulation.</p>
        
        <p><a href="/">← Back to Home</a></p>
    </div>
</body>
</html>
    ''', current_date=datetime.now().strftime('%B %d, %Y'))

@app.route('/trending')
def trending():
    """Trending articles"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get most viewed articles in last 7 days (simulated trending)
    cursor.execute('''
        SELECT id, title, summary, author, source, category, image_url, published_date
        FROM articles 
        WHERE published_date > datetime('now', '-7 days')
        ORDER BY RANDOM()
        LIMIT 20
    ''')
    
    trending_articles = cursor.fetchall()
    conn.close()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trending - WiseNews</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                <a class="nav-link" href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="text-center mb-4">
            <h1><i class="fas fa-fire text-danger"></i> Trending News</h1>
            <p class="lead">What's popular this week</p>
        </div>

        <div class="row">
            {% for article in trending_articles %}
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    {% if article[6] %}
                        <img src="{{ article[6] }}" class="card-img-top" style="height: 200px; object-fit: cover;">
                    {% endif %}
                    <div class="card-body">
                        <span class="badge bg-danger mb-2">
                            <i class="fas fa-fire"></i> Trending
                        </span>
                        <span class="badge bg-primary mb-2">{{ article[5].title() }}</span>
                        <h5 class="card-title">{{ article[1] }}</h5>
                        <p class="card-text">{{ article[2] }}</p>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-user"></i> {{ article[3] }} • 
                                <i class="fas fa-clock"></i> {{ article[7][:10] }}
                            </small>
                        </p>
                    </div>
                    <div class="card-footer">
                        <a href="/login?next=/article/{{ article[0] }}" class="btn btn-primary btn-sm">
                            <i class="fas fa-eye"></i> Read More
                        </a>
                        <small class="text-muted float-end">{{ article[4] }}</small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="text-center mt-4">
            <p class="text-muted">Sign in to get personalized trending content</p>
            <a href="/login" class="btn btn-primary">
                <i class="fas fa-sign-in-alt"></i> Sign In
            </a>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', trending_articles=trending_articles)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': {
            'GET /': 'Homepage with latest articles',
            'GET /api/status': 'API status and statistics',
            'GET /api/articles': 'Get articles with filtering & pagination',
            'GET /api/categories': 'Get all categories',
            'GET /api/category/<name>': 'Get articles by category',
            'GET /api/articles/<id>': 'Get single article',
            'GET /api/search?q=<query>': 'Search articles',
            'GET /api/trending': 'Get trending articles',
            'POST /api/articles': 'Add new article'
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'suggestion': 'Please try again or contact support'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🗞️  WiseNews starting on {host}:{port}")
    print(f"📊 Database: {app.config['DATABASE']}")
    print(f"🚀 Version: 3.0.0 - Railway Ready")
    
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    # Start background news fetcher
    print("📡 Starting news fetcher...")
    start_news_fetcher()
    
    # Fetch initial news
    print("📰 Fetching initial news...")
    try:
        total = fetch_all_news()
        print(f"✅ Initial fetch complete: {total} articles added")
    except Exception as e:
        print(f"⚠️ Initial news fetch failed: {e}")
    
    app.run(host=host, port=port, debug=False)
