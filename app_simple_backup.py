from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import sqlite3
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Configuration for Render
DATABASE = 'news_database.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            category TEXT DEFAULT 'General',
            published_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_name TEXT,
            url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample articles if database is empty
    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            ("Welcome to WiseNews", "WiseNews is your intelligent news aggregation platform. Stay informed with the latest news from technology, business, and more.", "WiseNews Team", "Technology"),
            ("Getting Started with WiseNews", "Learn how to navigate and make the most of your WiseNews experience. Discover features like search, categories, and personalization.", "WiseNews Team", "Guide"),
            ("Latest Technology Trends", "Explore the cutting-edge developments in artificial intelligence, machine learning, and emerging technologies shaping our future.", "Tech Reporter", "Technology"),
            ("Business Updates", "Stay current with market trends, startup news, and economic developments affecting the global business landscape.", "Business Analyst", "Business"),
            ("Feature Spotlight", "Discover the powerful features that make WiseNews your go-to source for intelligent news aggregation and analysis.", "Product Team", "Features")
        ]
        
        for title, content, author, category in sample_articles:
            cursor.execute('''
                INSERT INTO articles (title, content, author, category)
                VALUES (?, ?, ?, ?)
            ''', (title, content, author, category))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Homepage with featured articles"""
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        ORDER BY published_date DESC 
        LIMIT 6
    ''').fetchall()
    conn.close()
    
    return render_template('index.html', articles=articles)

@app.route('/articles')
def articles():
    """All articles page with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        ORDER BY published_date DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    total = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    conn.close()
    
    has_next = (page * per_page) < total
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
    conn.close()
    
    if article is None:
        return render_template('404.html'), 404
    
    return render_template('article_detail.html', article=article)

@app.route('/search')
def search():
    """Search articles"""
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', articles=[], query='')
    
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        WHERE title LIKE ? OR content LIKE ? OR author LIKE ?
        ORDER BY published_date DESC
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    return render_template('search.html', articles=articles, query=query)

@app.route('/category/<category>')
def category_articles(category):
    """Articles by category"""
    conn = get_db_connection()
    articles = conn.execute('''
        SELECT * FROM articles 
        WHERE category = ?
        ORDER BY published_date DESC
    ''', (category,)).fetchall()
    conn.close()
    
    return render_template('category.html', articles=articles, category=category)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# API Routes
@app.route('/api/status')
def api_status():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'message': 'WiseNews API is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/articles')
def api_articles():
    """Get all articles"""
    category = request.args.get('category')
    limit = request.args.get('limit', type=int)
    
    conn = get_db_connection()
    
    if category:
        query = 'SELECT * FROM articles WHERE category = ? ORDER BY published_date DESC'
        params = [category]
    else:
        query = 'SELECT * FROM articles ORDER BY published_date DESC'
        params = []
    
    if limit:
        query += ' LIMIT ?'
        params.append(limit)
    
    articles = conn.execute(query, params).fetchall()
    total = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    conn.close()
    
    return jsonify({
        'articles': [dict(article) for article in articles],
        'total': total,
        'count': len(articles)
    })

@app.route('/api/articles/<int:article_id>')
def api_article(article_id):
    """Get single article"""
    conn = get_db_connection()
    article = conn.execute('''
        SELECT * FROM articles WHERE id = ?
    ''', (article_id,)).fetchone()
    conn.close()
    
    if article is None:
        return jsonify({'error': 'Article not found'}), 404
    
    return jsonify(dict(article))

@app.route('/api/search')
def api_search():
    """Search articles API"""
    query = request.args.get('q', '')
    category = request.args.get('category')
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    conn = get_db_connection()
    
    if category:
        articles = conn.execute('''
            SELECT * FROM articles 
            WHERE (title LIKE ? OR content LIKE ? OR author LIKE ?) 
            AND category = ?
            ORDER BY published_date DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', category)).fetchall()
    else:
        articles = conn.execute('''
            SELECT * FROM articles 
            WHERE title LIKE ? OR content LIKE ? OR author LIKE ?
            ORDER BY published_date DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    
    conn.close()
    
    return jsonify({
        'articles': [dict(article) for article in articles],
        'query': query,
        'count': len(articles)
    })

@app.route('/api/categories')
def api_categories():
    """Get all categories with counts"""
    conn = get_db_connection()
    categories = conn.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'categories': [{'name': cat['category'], 'count': cat['count']} for cat in categories],
        'total_categories': len(categories)
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    
    # Get port from environment (Render/Railway/Heroku set this)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting WiseNews on {host}:{port}")
    
    # Run the application
    app.run(host=host, port=port, debug=False)
