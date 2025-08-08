from flask import Flask, jsonify, render_template, request
import os
import sqlite3
import requests
from datetime import datetime
import feedparser
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
        'timestamp': datetime.now().isoformat()
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

@app.route('/api/fetch-news')
def fetch_news():
    """Fetch news from RSS feeds"""
    try:
        # Sample RSS feeds for testing
        rss_feeds = [
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://rss.reuters.com/reuters/topNews'
        ]
        
        articles_added = 0
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                source = feed.feed.get('title', 'Unknown Source')
                
                for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO articles (title, content, url, source, published_date)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            entry.title,
                            entry.get('summary', '')[:1000],  # Limit content length
                            entry.link,
                            source,
                            entry.get('published', datetime.now().isoformat())
                        ))
                        if cursor.rowcount > 0:
                            articles_added += 1
                    except Exception as e:
                        print(f"Error adding article: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error parsing feed {feed_url}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully fetched {articles_added} new articles',
            'articles_added': articles_added
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching news: {str(e)}'
        }), 500

@app.route('/api/search')
def search_articles():
    """Search articles by keyword"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Please provide a search query'
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

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            '/',
            '/api/status',
            '/api/articles',
            '/api/fetch-news',
            '/api/search?q=keyword'
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
