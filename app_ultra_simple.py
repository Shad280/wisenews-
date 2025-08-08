#!/usr/bin/env python3
"""
Ultra-Simple Railway Test - No Database Dependencies
"""

from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Ultra-simple homepage"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Ultra-Simple Railway Test</title>
    <style>
        body { font-family: Arial; margin: 50px; }
        .success { color: green; }
        .error { color: red; }
        .info { background: #e1f5fe; padding: 20px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🚀 Ultra-Simple Railway Test</h1>
    <div class="info">
        <h3>✅ SUCCESS: Railway deployment is working!</h3>
        <p>This confirms the basic Flask app can run on Railway.</p>
        <p><strong>Issue Analysis:</strong> The login problem is likely:</p>
        <ul>
            <li>❌ Railway database is empty (no admin user)</li>
            <li>❌ Database initialization failing silently</li>
            <li>❌ bcrypt dependencies missing on Railway</li>
        </ul>
    </div>
    <div>
        <h3>🔍 Next Steps:</h3>
        <ol>
            <li>Confirm this simple app works</li>
            <li>Add database creation step by step</li>
            <li>Test login with hardcoded credentials first</li>
        </ol>
    </div>
    <div>
        <h3>📋 Test Status:</h3>
        <p><strong>App Status:</strong> <span class="success">✅ Running</span></p>
        <p><strong>Database:</strong> <span class="error">❌ Not tested yet</span></p>
        <p><strong>Authentication:</strong> <span class="error">❌ Not tested yet</span></p>
    </div>
</body>
</html>
    '''

@app.route('/test')
def test():
    """Test endpoint"""
    return {
        'status': 'success',
        'message': 'Ultra-simple Railway test working!',
        'diagnosis': 'If you see this, basic Flask is working on Railway'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🚀 Ultra-Simple Railway Test Starting...")
    print(f"✅ Running on {host}:{port}")
    print("🎯 This should work if Railway Flask deployment is OK")
    
    app.run(host=host, port=port, debug=False)
