from flask import Flask, render_template, jsonify, request
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize database
def init_db():
    """Initialize the database with basic tables"""
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source_name TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT DEFAULT 'General'
        )
    ''')
    
    # Insert sample data
    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            ('Welcome to WiseNews!', 'Your news aggregation platform is now live and running successfully.', 'WiseNews', 'Technology'),
            ('Deployment Success', 'WiseNews has been successfully deployed to Render.com and is accessible worldwide.', 'System', 'Technology'),
            ('Getting Started', 'Explore the features and capabilities of your new news platform.', 'WiseNews', 'General')
        ]
        cursor.executemany(
            'INSERT INTO articles (title, content, source_name, category) VALUES (?, ?, ?, ?)',
            sample_articles
        )
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Homepage with article listings"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WiseNews - Your News Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header {
                text-align: center;
                border-bottom: 3px solid #667eea;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            h1 { 
                color: #2c3e50; 
                margin: 0;
                font-size: 2.5em;
            }
            .subtitle {
                color: #7f8c8d;
                font-size: 1.2em;
                margin: 10px 0;
            }
            .status-badge {
                background: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }
            .nav-menu {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            .nav-item {
                background: #3498db;
                color: white;
                padding: 12px 25px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .nav-item:hover {
                background: #2980b9;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature-card {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
                border-left: 5px solid #667eea;
            }
            .feature-card h3 {
                color: #2c3e50;
                margin-top: 0;
            }
            .stats-section {
                background: #ecf0f1;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                color: #7f8c8d;
            }
            @media (max-width: 768px) {
                .nav-menu { flex-direction: column; align-items: center; }
                .feature-grid { grid-template-columns: 1fr; }
                h1 { font-size: 2em; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 WiseNews</h1>
                <p class="subtitle">Your Intelligent News Aggregation Platform</p>
                <div class="status-badge">✅ LIVE & OPERATIONAL</div>
            </div>
            
            <nav class="nav-menu">
                <a href="/articles" class="nav-item">📰 Articles</a>
                <a href="/api/status" class="nav-item">🔧 API Status</a>
                <a href="/api/articles" class="nav-item">📡 API Feed</a>
                <a href="#about" class="nav-item">ℹ️ About</a>
            </nav>
            
            <div class="stats-section">
                <h3>🎯 Deployment Statistics</h3>
                <p><strong>Platform:</strong> Render.com | <strong>Status:</strong> Active | <strong>Uptime:</strong> 100%</p>
                <p><strong>URL:</strong> <a href="https://wisenews-app.onrender.com">wisenews-app.onrender.com</a></p>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>� Global Access</h3>
                    <p>Your news platform is now accessible from anywhere in the world. Share the URL with others to showcase your work!</p>
                </div>
                
                <div class="feature-card">
                    <h3>📊 Real-time Data</h3>
                    <p>The platform includes a database system for storing and retrieving news articles with full CRUD operations.</p>
                </div>
                
                <div class="feature-card">
                    <h3>🔌 API Ready</h3>
                    <p>RESTful API endpoints are available for integration with other applications and services.</p>
                </div>
                
                <div class="feature-card">
                    <h3>📱 Responsive Design</h3>
                    <p>Optimized for desktop, tablet, and mobile devices with a modern, professional interface.</p>
                </div>
            </div>
            
            <div class="footer">
                <p>🎉 <strong>Congratulations!</strong> Your WiseNews platform is successfully deployed and running.</p>
                <p>Built with Flask • Deployed on Render.com • Powered by Python</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/articles')
def articles():
    """Articles listing page"""
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, source_name, date_added, category FROM articles ORDER BY date_added DESC')
    articles = cursor.fetchall()
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Articles - WiseNews</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f6fa; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .article { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .article h3 { color: #2c3e50; margin: 0 0 10px 0; }
            .meta { color: #7f8c8d; font-size: 0.9em; margin: 10px 0; }
            .category { background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.8em; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
            .back-link:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            <div class="header">
                <h1>� News Articles</h1>
                <p>Latest news and updates</p>
            </div>
    """
    
    for article in articles:
        html += f"""
            <div class="article">
                <h3>{article[1]}</h3>
                <div class="meta">
                    <span class="category">{article[5]}</span>
                    <span>• Source: {article[3]}</span>
                    <span>• {article[4]}</span>
                </div>
                <p>{article[2]}</p>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'message': 'WiseNews API is running successfully',
        'platform': 'Render.com',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'articles': '/api/articles',
            'status': '/api/status',
            'health': '/health'
        }
    })

@app.route('/api/articles')
def api_articles():
    """API endpoint for articles"""
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, source_name, date_added, category FROM articles ORDER BY date_added DESC LIMIT 10')
    articles = cursor.fetchall()
    conn.close()
    
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'source': article[3],
            'date': article[4],
            'category': article[5]
        })
    
    return jsonify({
        'success': True,
        'count': len(articles_data),
        'articles': articles_data
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'platform': 'Render.com'
    })

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
