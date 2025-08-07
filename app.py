from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import sqlite3
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'wisenews-secret-key-2025')

# Configuration
DATABASE = 'news_database.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with all required tables"""
    conn = get_db_connection()
    
    # Create articles table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source_name TEXT,
            url TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT DEFAULT 'General',
            keywords TEXT,
            image_url TEXT
        )
    ''')
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Create bookmarks table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    ''')
    
    # Insert sample data if articles table is empty
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            (
                'Welcome to WiseNews - Your Intelligent News Platform!', 
                'WiseNews is now successfully deployed and running on Render.com! This powerful news aggregation platform brings you the latest updates from around the world with advanced features including user authentication, bookmarking, search functionality, and much more. Your journey into intelligent news consumption starts here.',
                'WiseNews System', 
                'https://wisenews-app.onrender.com',
                'Technology',
                'wisenews,deployment,news,platform,technology',
                'https://via.placeholder.com/300x200/2196F3/white?text=WiseNews'
            ),
            (
                'Deployment Success: WiseNews Goes Live!', 
                'After careful development and testing, WiseNews has been successfully deployed to the cloud. The platform now features a complete news aggregation system with user management, real-time updates, and a responsive design that works perfectly on all devices. This marks a significant milestone in bringing intelligent news curation to users worldwide.',
                'Deployment Team', 
                'https://wisenews-app.onrender.com/about',
                'Technology',
                'deployment,success,cloud,responsive,milestone',
                'https://via.placeholder.com/300x200/27ae60/white?text=SUCCESS'
            ),
            (
                'Advanced Features Now Available', 
                'WiseNews comes packed with advanced features including intelligent article categorization, powerful search functionality, user bookmarking system, and a clean, intuitive interface. The platform is designed to grow with your needs, offering scalability and performance that can handle increasing user demands.',
                'Feature Team', 
                'https://wisenews-app.onrender.com/features',
                'Features',
                'features,search,bookmarks,scalability,performance',
                'https://via.placeholder.com/300x200/9b59b6/white?text=FEATURES'
            ),
            (
                'Getting Started with WiseNews', 
                'New to WiseNews? Getting started is easy! Simply browse articles on the homepage, use the search function to find specific topics, create an account to bookmark your favorite articles, and explore different categories to discover content that interests you. The platform is designed to be intuitive and user-friendly.',
                'User Guide', 
                'https://wisenews-app.onrender.com/help',
                'Guide',
                'tutorial,getting started,user guide,browse,search',
                'https://via.placeholder.com/300x200/f39c12/white?text=GUIDE'
            ),
            (
                'Real-time News Updates Coming Soon', 
                'We are working on exciting new features including real-time news updates, push notifications, social media integration, and advanced analytics. Stay tuned for these upcoming enhancements that will make WiseNews even more powerful and engaging for our users.',
                'Development Team', 
                'https://wisenews-app.onrender.com/roadmap',
                'Updates',
                'real-time,notifications,social media,analytics,roadmap',
                'https://via.placeholder.com/300x200/e74c3c/white?text=UPDATES'
            )
        ]
        
        conn.executemany('''
            INSERT INTO articles (title, content, source_name, url, category, keywords, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_articles)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Homepage with featured articles"""
    conn = get_db_connection()
    
    # Get featured articles
    articles = conn.execute('''
        SELECT * FROM articles 
        ORDER BY date_added DESC 
        LIMIT 6
    ''').fetchall()
    
    # Get statistics for homepage
    total_articles = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    
    # Get categories with counts
    categories_data = conn.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
    ''').fetchall()
    
    # Get recent articles
    recent_articles = conn.execute('''
        SELECT * FROM articles 
        ORDER BY date_added DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    # Prepare data for template
    categories = [(cat['category'], cat['count']) for cat in categories_data]
    total_categories = len(categories)
    current_time = datetime.now()
    
    return render_template('index.html', 
                         featured_articles=articles,
                         total_articles=total_articles,
                         total_categories=total_categories,
                         categories=categories,
                         recent_articles=recent_articles,
                         current_time=current_time)

@app.route('/articles')
def articles():
    """All articles page with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        ORDER BY date_added DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    total = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    conn.close()
    
    has_next = offset + per_page < total
    has_prev = page > 1
    
    return render_template('articles.html', 
                         articles=articles, 
                         page=page,
                         has_next=has_next, 
                         has_prev=has_prev)

@app.route('/article/<int:article_id>')
def view_article(article_id):
    """View individual article"""
    conn = get_db_connection()
    article = conn.execute('''
        SELECT * FROM articles WHERE id = ?
    ''', (article_id,)).fetchone()
    
    if article is None:
        conn.close()
        flash('Article not found.', 'error')
        return redirect(url_for('articles'))
    
    # Get related articles from same category
    related_articles = conn.execute('''
        SELECT * FROM articles 
        WHERE category = ? AND id != ?
        ORDER BY date_added DESC 
        LIMIT 3
    ''', (article['category'], article_id)).fetchall()
    
    conn.close()
    
    return render_template('article_detail.html', 
                         article=article, 
                         related_articles=related_articles)

@app.route('/search')
def search():
    """Search articles"""
    query = request.args.get('q', '')
    category = request.args.get('category')
    
    conn = get_db_connection()
    
    if query:
        # Search articles
        if category:
            articles = conn.execute('''
                SELECT * FROM articles 
                WHERE (title LIKE ? OR content LIKE ? OR keywords LIKE ?) AND category = ?
                ORDER BY date_added DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', category)).fetchall()
        else:
            articles = conn.execute('''
                SELECT * FROM articles 
                WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
                ORDER BY date_added DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        
        # Get category counts for filters
        category_counts = []
        if articles:
            categories = conn.execute('''
                SELECT category, COUNT(*) as count 
                FROM articles 
                WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
                GROUP BY category 
                ORDER BY count DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
            category_counts = [(cat['category'], cat['count']) for cat in categories]
    else:
        articles = []
        category_counts = []
    
    conn.close()
    
    return render_template('search.html', 
                         results=articles, 
                         query=query,
                         category_counts=category_counts)

@app.route('/category/<category>')
def category_articles(category):
    """Articles by category"""
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        WHERE category = ?
        ORDER BY date_added DESC
    ''', (category,)).fetchall()
    conn.close()
    
    return render_template('category.html', articles=articles, category=category)

@app.route('/about')
def about():
    """About page"""
    conn = get_db_connection()
    total_articles = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    total_categories = conn.execute('SELECT COUNT(DISTINCT category) FROM articles').fetchone()[0]
    conn.close()
    
    return render_template('about.html', 
                         total_articles=total_articles,
                         total_categories=total_categories)

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# API Routes
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'message': 'WiseNews API is running successfully',
        'platform': 'Render.com',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'articles': True,
            'search': True,
            'categories': True,
            'bookmarks': True
        }
    })

@app.route('/api/articles')
def api_articles():
    """API endpoint for articles"""
    limit = request.args.get('limit', 20, type=int)
    category = request.args.get('category')
    
    conn = get_db_connection()
    
    if category:
        articles = conn.execute('''
            SELECT * FROM articles 
            WHERE category = ?
            ORDER BY date_added DESC 
            LIMIT ?
        ''', (category, limit)).fetchall()
    else:
        articles = conn.execute('''
            SELECT * FROM articles 
            ORDER BY date_added DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
    
    conn.close()
    
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article['id'],
            'title': article['title'],
            'content': article['content'][:200] + '...' if len(article['content']) > 200 else article['content'],
            'source': article['source_name'],
            'url': article['url'],
            'date': article['date_added'],
            'category': article['category'],
            'keywords': article['keywords'].split(',') if article['keywords'] else [],
            'image_url': article['image_url']
        })
    
    return jsonify({
        'success': True,
        'count': len(articles_data),
        'articles': articles_data
    })

@app.route('/api/search')
def api_search():
    """API search endpoint"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'success': False, 'message': 'No search query provided'})
    
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
        ORDER BY date_added DESC
        LIMIT 50
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article['id'],
            'title': article['title'],
            'content': article['content'][:200] + '...' if len(article['content']) > 200 else article['content'],
            'source': article['source_name'],
            'category': article['category'],
            'date': article['date_added']
        })
    
    return jsonify({
        'success': True,
        'query': query,
        'count': len(articles_data),
        'articles': articles_data
    })

@app.route('/api/categories')
def api_categories():
    """API endpoint for categories"""
    conn = get_db_connection()
    categories = conn.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
    ''').fetchall()
    conn.close()
    
    categories_data = []
    for cat in categories:
        categories_data.append({
            'name': cat['category'],
            'count': cat['count']
        })
    
    return jsonify({
        'success': True,
        'categories': categories_data
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'platform': 'Render.com'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Initialize database on startup
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # For production (Gunicorn)
    init_db()

    
