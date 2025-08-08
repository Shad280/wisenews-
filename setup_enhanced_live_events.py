"""
Live Events Enhancement Integration Script
Complete setup and installation guide for WebSocket-based live events
"""

import os
import subprocess
import sys

def install_dependencies():
    """Install required packages for enhanced live events"""
    print("📦 Installing required dependencies...")
    
    required_packages = [
        'flask-socketio>=5.3.0',
        'python-socketio>=5.7.0',
        'websockets>=10.4',
        'gevent>=22.10.0',
        'redis>=4.3.4',  # For production scaling
        'psutil>=5.9.0'  # For system monitoring
    ]
    
    for package in required_packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def update_requirements_file():
    """Update requirements.txt with new dependencies"""
    print("📝 Updating requirements.txt...")
    
    new_requirements = [
        'flask-socketio>=5.3.0',
        'python-socketio>=5.7.0', 
        'websockets>=10.4',
        'gevent>=22.10.0',
        'redis>=4.3.4',
        'psutil>=5.9.0'
    ]
    
    try:
        # Read existing requirements
        with open('requirements.txt', 'r') as f:
            existing = f.read().splitlines()
        
        # Add new requirements if not already present
        updated = existing.copy()
        for req in new_requirements:
            package_name = req.split('>=')[0]
            if not any(package_name in line for line in existing):
                updated.append(req)
        
        # Write updated requirements
        with open('requirements.txt', 'w') as f:
            f.write('\n'.join(updated) + '\n')
        
        print("✅ requirements.txt updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update requirements.txt: {e}")
        return False

def create_integration_template():
    """Create template for integrating enhanced live events"""
    
    integration_code = '''"""
Integration code for enhanced live events
Add this to your main app.py file
"""

# Add these imports at the top of app.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from enhanced_live_events import EnhancedLiveEventsManager
import threading

# Initialize SocketIO (add after Flask app creation)
socketio = SocketIO(app, cors_allowed_origins="*", 
                   async_mode='gevent',
                   ping_timeout=60,
                   ping_interval=25)

# Initialize enhanced live events manager
enhanced_live_events = EnhancedLiveEventsManager(socketio)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_confirmed', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    enhanced_live_events.handle_user_disconnect(request.sid)

@socketio.on('join_event')
def handle_join_event(data):
    """Handle user joining an event room"""
    event_id = data.get('event_id')
    user_id = data.get('user_id', 1)
    
    if event_id:
        enhanced_live_events.subscribe_user(user_id, event_id, request.sid)
        join_room(f'event_{event_id}')
        emit('subscription_confirmed', {
            'event_id': event_id,
            'status': 'subscribed'
        })

@socketio.on('leave_event')
def handle_leave_event(data):
    """Handle user leaving an event room"""
    event_id = data.get('event_id')
    user_id = data.get('user_id', 1)
    
    if event_id:
        enhanced_live_events.unsubscribe_user(user_id, event_id)
        leave_room(f'event_{event_id}')
        emit('subscription_cancelled', {
            'event_id': event_id,
            'status': 'unsubscribed'
        })

@socketio.on('request_event_status')
def handle_event_status_request(data):
    """Handle request for current event status"""
    event_id = data.get('event_id')
    if event_id:
        status = enhanced_live_events.get_event_status(event_id)
        emit('event_status', status)

# Update your live events routes
@app.route('/live-events')
def live_events_page():
    """Enhanced live events page with WebSocket support"""
    try:
        # Get active events
        events = enhanced_live_events.get_active_events()
        
        # Get user subscriptions
        user_id = session.get('user_id', 1)
        subscriptions = enhanced_live_events.get_user_subscriptions(user_id)
        
        return render_template('live_events.html', 
                             events=events,
                             subscriptions=subscriptions,
                             websocket_enabled=True)
    except Exception as e:
        logger.error(f"Error loading live events: {e}")
        return render_template('error.html', error="Failed to load live events")

# Background event processor
def start_background_processors():
    """Start background processors for live events"""
    def run_processor():
        enhanced_live_events.start_background_processor()
    
    processor_thread = threading.Thread(target=run_processor, daemon=True)
    processor_thread.start()

# Performance monitoring endpoint
@app.route('/api/live-events/performance')
def live_events_performance():
    """Get live events performance metrics"""
    metrics = enhanced_live_events.get_performance_metrics()
    return jsonify(metrics)

# Start background processors when app starts
start_background_processors()

# Update your main run block
if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5000,
                allow_unsafe_werkzeug=True)
'''
    
    try:
        with open('live_events_integration.py', 'w') as f:
            f.write(integration_code)
        print("✅ Integration template created: live_events_integration.py")
        return True
    except Exception as e:
        print(f"❌ Failed to create integration template: {e}")
        return False

def create_html_template():
    """Create enhanced HTML template for live events"""
    
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Events - Enhanced</title>
    
    <!-- Socket.IO Client -->
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Custom CSS will be injected by JavaScript -->
    <style>
        body { 
            background-color: #f8f9fa; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .navbar { 
            box-shadow: 0 2px 4px rgba(0,0,0,.1); 
        }
        .page-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body data-user-id="{{ session.get('user_id', 1) }}">
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">📰 WiseNews</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link active" href="/live-events">Live Events</a>
            </div>
        </div>
    </nav>

    <!-- Page Title -->
    <div class="page-title">
        <div class="container">
            <h1 class="mb-0">🔴 Live Events</h1>
            <p class="mb-0 mt-2">Real-time updates and breaking news</p>
        </div>
    </div>

    <!-- Connection Status -->
    <div class="connection-status">🔴 Connecting...</div>

    <!-- Main Content -->
    <div class="container live-events-container">
        {% if events %}
            <div class="row">
                {% for event in events %}
                <div class="col-lg-6 mb-4">
                    <div class="event-card" data-event-id="{{ event.id }}">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div>
                                <h4 class="card-title mb-1">{{ event.title }}</h4>
                                <p class="text-muted mb-0">{{ event.category }}</p>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                <span class="live-indicator"></span>
                                <small class="text-success fw-bold">LIVE</small>
                            </div>
                        </div>
                        
                        <p class="card-text">{{ event.description }}</p>
                        
                        <div class="event-stats">
                            <span class="stat-item">
                                <i class="bi bi-clock"></i>
                                Started: {{ event.start_time.strftime('%H:%M') }}
                            </span>
                            <span class="stat-item">
                                <i class="bi bi-people"></i>
                                {{ event.priority.title() }} Priority
                            </span>
                        </div>
                        
                        <div class="mt-3">
                            {% if event.id in subscriptions %}
                                <button class="btn btn-secondary subscription-btn leave-event-btn" 
                                        data-event-id="{{ event.id }}">
                                    🔕 Unsubscribe
                                </button>
                            {% else %}
                                <button class="btn btn-primary subscription-btn join-event-btn" 
                                        data-event-id="{{ event.id }}">
                                    🔔 Subscribe
                                </button>
                            {% endif %}
                        </div>
                        
                        <div class="live-updates mt-4">
                            <h6>📺 Live Updates</h6>
                            {% for update in event.recent_updates %}
                            <div class="update-item priority-{{ update.priority }}">
                                <div class="update-header">
                                    <span class="update-icons">
                                        {% if update.priority == 'critical' %}🔴{% elif update.priority == 'high' %}🟠{% else %}🟡{% endif %}
                                        📝
                                    </span>
                                    <span class="update-time">{{ update.timestamp.strftime('%H:%M:%S') }}</span>
                                </div>
                                <div class="update-content">{{ update.content }}</div>
                            </div>
                            {% endfor %}
                        </div>
                        
                        <div class="last-updated mt-2">
                            Last updated: {{ event.last_updated.strftime('%H:%M:%S') if event.last_updated else 'Never' }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-center py-5">
                <h3>📭 No Live Events</h3>
                <p class="text-muted">There are currently no active live events. Check back later!</p>
            </div>
        {% endif %}
    </div>

    <!-- Performance Metrics (Debug) -->
    <div class="performance-metrics" style="display: none;">
        <div>WebSocket: <span id="ws-status">Disconnected</span></div>
        <div>Updates/min: <span id="updates-rate">0</span></div>
        <div>Active Events: <span id="active-events">0</span></div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Include our enhanced live events JavaScript -->
    <script>
        // This will be populated from live_events_frontend.py
        window.currentUserId = {{ session.get('user_id', 1) }};
    </script>
    
    <!-- The JavaScript from live_events_frontend.py will be injected here -->
    {{ enhanced_js|safe }}
</body>
</html>'''
    
    try:
        os.makedirs('templates', exist_ok=True)
        with open('templates/live_events_enhanced.html', 'w') as f:
            f.write(html_template)
        print("✅ Enhanced HTML template created: templates/live_events_enhanced.html")
        return True
    except Exception as e:
        print(f"❌ Failed to create HTML template: {e}")
        return False

def create_deployment_script():
    """Create deployment script for production"""
    
    deployment_script = '''#!/bin/bash
# Enhanced Live Events Deployment Script

echo "🚀 Deploying Enhanced Live Events..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup Redis (for production scaling)
echo "🔧 Setting up Redis..."
# Uncomment for Linux/Mac:
# sudo apt-get install redis-server
# redis-server --daemonize yes

# For Windows, download Redis from: https://github.com/microsoftarchive/redis/releases

# Create database tables
echo "🗃️ Setting up database..."
python -c "
import sqlite3
conn = sqlite3.connect('news_database.db')
cursor = conn.cursor()

# Create enhanced tables if they do not exist
cursor.execute('''CREATE TABLE IF NOT EXISTS live_event_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES live_events (id)
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS websocket_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER,
    connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_ping DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)''')

conn.commit()
conn.close()
print('Database setup complete')
"

# Test WebSocket functionality
echo "🧪 Testing WebSocket functionality..."
python -c "
try:
    import socketio
    import flask_socketio
    print('✅ SocketIO libraries available')
except ImportError as e:
    print(f'❌ Missing dependencies: {e}')
    exit(1)
"

echo "✅ Enhanced Live Events deployment complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Update your app.py with the integration code from live_events_integration.py"
echo "2. Replace your live events template with templates/live_events_enhanced.html"
echo "3. Test the WebSocket connection"
echo "4. Monitor performance metrics"
echo ""
echo "🌐 For production deployment:"
echo "- Consider using Redis for scaling across multiple servers"
echo "- Set up proper WebSocket load balancing"
echo "- Monitor connection limits and performance"
'''
    
    try:
        with open('deploy_enhanced_live_events.sh', 'w') as f:
            f.write(deployment_script)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod('deploy_enhanced_live_events.sh', 0o755)
        
        print("✅ Deployment script created: deploy_enhanced_live_events.sh")
        return True
    except Exception as e:
        print(f"❌ Failed to create deployment script: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Enhanced Live Events Setup")
    print("=" * 50)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Install dependencies
    if install_dependencies():
        success_count += 1
    
    # Step 2: Update requirements.txt
    if update_requirements_file():
        success_count += 1
    
    # Step 3: Create integration template
    if create_integration_template():
        success_count += 1
    
    # Step 4: Create HTML template
    if create_html_template():
        success_count += 1
    
    # Step 5: Create deployment script
    if create_deployment_script():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Setup Complete: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 All components installed successfully!")
        print("\n📋 Next Steps:")
        print("1. Review live_events_integration.py for app.py integration")
        print("2. Update your live events template with the enhanced version")
        print("3. Test WebSocket connectivity")
        print("4. Monitor performance metrics")
    else:
        print("⚠️ Some components failed to install. Please check the errors above.")

if __name__ == "__main__":
    main()
