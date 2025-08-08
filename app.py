from flask import Flask, jsonify, request, render_template_string
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
    """Homepage with latest news"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get latest 20 articles
        cursor.execute('''
            SELECT a.*, c.color as category_color
            FROM articles a 
            LEFT JOIN categories c ON a.category = c.name
            ORDER BY a.created_at DESC 
            LIMIT 20
        ''')
        articles = cursor.fetchall()
        
        # Get categories for navigation
        cursor.execute('SELECT * FROM categories ORDER BY name')
        categories = cursor.fetchall()
        
        conn.close()
        
        # Return HTML page instead of JSON
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiseNews - Your Smart News Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; color: #007bff !important; }
        .article-card { transition: transform 0.2s; }
        .article-card:hover { transform: translateY(-5px); }
        .category-badge { font-size: 0.8em; }
        .hero-section { background: linear-gradient(135deg, #007bff, #28a745); color: white; padding: 60px 0; }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fas fa-newspaper"></i> WiseNews</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                    {% for category in categories %}
                    <li class="nav-item">
                        <a class="nav-link" href="/category/{{ category.name }}">{{ category.description }}</a>
                    </li>
                    {% endfor %}
                </ul>
                <form class="d-flex" action="/search" method="GET">
                    <input class="form-control me-2" type="search" name="q" placeholder="Search news...">
                    <button class="btn btn-outline-success" type="submit">Search</button>
                </form>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <div class="hero-section text-center">
        <div class="container">
            <h1 class="display-4"><i class="fas fa-newspaper"></i> WiseNews</h1>
            <p class="lead">Your Smart News Platform - Stay Informed, Stay Wise</p>
            <p>Latest news from around the world, categorized and ready to read</p>
        </div>
    </div>

    <!-- Articles Section -->
    <div class="container mt-5">
        <h2 class="mb-4"><i class="fas fa-clock"></i> Latest News</h2>
        <div class="row">
            {% for article in articles %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card article-card h-100">
                    <img src="{{ article.image_url }}" class="card-img-top" alt="{{ article.title }}" style="height: 200px; object-fit: cover;">
                    <div class="card-body">
                        <span class="badge category-badge mb-2" style="background-color: {{ article.category_color }}">{{ article.category.title() }}</span>
                        <h5 class="card-title">{{ article.title }}</h5>
                        <p class="card-text">{{ article.summary }}</p>
                        <p class="card-text"><small class="text-muted">By {{ article.author }} • {{ article.created_at }}</small></p>
                    </div>
                    <div class="card-footer">
                        <a href="/article/{{ article.id }}" class="btn btn-primary">Read More</a>
                        <small class="text-muted float-end"><i class="fas fa-eye"></i> {{ article.read_count }} reads</small>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-light mt-5 py-4">
        <div class="container text-center">
            <p>&copy; 2025 WiseNews. Your Smart News Platform. Version 3.0.0</p>
            <p><a href="/api/articles" class="text-light">API</a> | <a href="/trending" class="text-light">Trending</a></p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', articles=articles, categories=categories)
        
    except Exception as e:
        return f"<h1>Error loading homepage: {str(e)}</h1>", 500

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
