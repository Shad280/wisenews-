from flask import Flask, render_template, request, jsonify, send_file
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wisenews-secure-key-2025'

# Database setup
def init_db():
    conn = sqlite3.connect('news_database.db')
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
            read_status BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'message': 'WiseNews is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/articles')
def articles():
    """Browse all articles"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, source_type, source_name, category, date_added
            FROM articles 
            ORDER BY date_added DESC 
            LIMIT 50
        ''')
        articles_data = cursor.fetchall()
        conn.close()
        return jsonify({
            'status': 'success',
            'articles': [
                {
                    'id': row[0],
                    'title': row[1],
                    'source_type': row[2],
                    'source_name': row[3],
                    'category': row[4],
                    'date_added': row[5]
                } for row in articles_data
            ]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
