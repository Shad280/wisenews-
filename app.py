from flask import Flask, jsonify, request
import os
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT,
            published_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add some sample articles if table is empty
    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            ('Breaking: Tech Innovation Reaches New Heights', 'Technology companies continue to push boundaries with revolutionary new products and services.', 'https://example.com/tech-news-1', 'TechNews', '2025-08-08'),
            ('Global Markets Show Strong Performance', 'International financial markets demonstrate resilience amid economic uncertainties.', 'https://example.com/market-news-1', 'FinanceDaily', '2025-08-08'),
            ('Climate Action Summit Yields Promising Results', 'World leaders commit to ambitious new environmental protection measures.', 'https://example.com/climate-news-1', 'GreenWorld', '2025-08-08'),
            ('Healthcare Breakthrough: New Treatment Options', 'Medical researchers announce significant advances in disease treatment and prevention.', 'https://example.com/health-news-1', 'MedicalToday', '2025-08-08'),
            ('Education Technology Transforms Learning', 'Innovative educational platforms revolutionize how students access and engage with knowledge.', 'https://example.com/edu-news-1', 'EduTech Weekly', '2025-08-08')
        ]
        cursor.executemany('''
            INSERT INTO articles (title, content, url, source, published_date)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_articles)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Main page showing latest news"""
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles ORDER BY created_at DESC LIMIT 10')
        articles = cursor.fetchall()
        conn.close()
        
        # Convert to dictionaries for easier handling
        articles_list = []
        for article in articles:
            articles_list.append({
                'id': article[0],
                'title': article[1],
                'content': article[2],
                'url': article[3],
                'source': article[4],
                'published_date': article[5],
                'created_at': article[6]
            })
        
        return jsonify({
            'status': 'success',
            'message': 'WiseNews - Latest Articles',
            'version': '2.0.1',
            'articles_count': len(articles_list),
            'articles': articles_list
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching articles: {str(e)}'
        }), 500

@app.route('/api/status')
def api_status():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.1',
        'message': 'WiseNews API is running',
        'deployment': 'production',
        'timestamp': datetime.now().isoformat(),
        'features': ['SQLite Database', 'Article Storage', 'Search', 'Sample Data']
    })

@app.route('/api/articles')
def get_articles():
    """Get all articles"""
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles ORDER BY created_at DESC')
        articles = cursor.fetchall()
        conn.close()
        
        articles_list = []
        for article in articles:
            articles_list.append({
                'id': article[0],
                'title': article[1],
                'content': article[2][:200] + '...' if len(article[2] or '') > 200 else article[2],
                'url': article[3],
                'source': article[4],
                'published_date': article[5],
                'created_at': article[6]
            })
        
        return jsonify({
            'status': 'success',
            'count': len(articles_list),
            'articles': articles_list
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/search')
def search_articles():
    """Search articles by keyword"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Please provide a search query using ?q=keyword'
        }), 400
    
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM articles 
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%'))
        articles = cursor.fetchall()
        conn.close()
        
        articles_list = []
        for article in articles:
            articles_list.append({
                'id': article[0],
                'title': article[1],
                'content': article[2][:200] + '...' if len(article[2] or '') > 200 else article[2],
                'url': article[3],
                'source': article[4],
                'published_date': article[5],
                'created_at': article[6]
            })
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(articles_list),
            'articles': articles_list
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Search error: {str(e)}'
        }), 500

@app.route('/api/add-article', methods=['POST'])
def add_article():
    """Add a new article"""
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({
                'status': 'error',
                'message': 'Title is required'
            }), 400
        
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO articles (title, content, url, source, published_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('content', ''),
            data.get('url', ''),
            data.get('source', 'User Submitted'),
            data.get('published_date', datetime.now().isoformat())
        ))
        conn.commit()
        article_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Article added successfully',
            'article_id': article_id
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding article: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /api/status',
            'GET /api/articles',
            'GET /api/search?q=keyword',
            'POST /api/add-article'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
