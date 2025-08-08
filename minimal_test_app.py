#!/usr/bin/env python3
"""
Minimal Railway Test App
Test if basic Flask app works on Railway
"""

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>🎉 WiseNews Railway Test - SUCCESS!</h1>
    <p>If you see this, Railway is working correctly.</p>
    <p>The issue is in the main WiseNews app, not Railway itself.</p>
    <hr>
    <p><strong>Next step:</strong> Check Railway logs to see WiseNews startup errors.</p>
    <p><strong>URL:</strong> https://web-production-1f6d.up.railway.app/</p>
    '''

@app.route('/test')
def test():
    return {'status': 'Railway connection working', 'app': 'minimal-test'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🧪 Minimal test app starting on {host}:{port}")
    app.run(host=host, port=port, debug=False)
