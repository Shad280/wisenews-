from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'WiseNews is working!',
        'message': 'This is a minimal test deployment',
        'timestamp': '2025-08-08'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'message': 'WiseNews API is running',
        'deployment': 'minimal test'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
