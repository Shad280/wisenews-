"""
Simple Enhanced Live Events Setup Script
"""

import subprocess
import sys
import os

def install_required_packages():
    """Install the required packages for enhanced live events"""
    print("📦 Installing required packages...")
    
    packages = [
        'flask-socketio',
        'python-socketio', 
        'websockets',
        'gevent',
        'psutil'
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing {package}: {e}")

def setup_database():
    """Setup additional database tables for enhanced live events"""
    print("🗃️ Setting up database tables...")
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Create live event metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_event_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                metric_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create websocket sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS websocket_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER,
                connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_ping DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

def update_requirements():
    """Update requirements.txt with new dependencies"""
    print("📝 Updating requirements.txt...")
    
    new_packages = [
        'flask-socketio>=5.3.0',
        'python-socketio>=5.7.0',
        'websockets>=10.4',
        'gevent>=22.10.0',
        'psutil>=5.9.0'
    ]
    
    try:
        # Read existing requirements
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                existing = f.read()
        else:
            existing = ""
        
        # Add new packages if not already present
        for package in new_packages:
            package_name = package.split('>=')[0]
            if package_name not in existing:
                existing += f"\n{package}"
        
        # Write updated requirements
        with open('requirements.txt', 'w') as f:
            f.write(existing.strip() + "\n")
        
        print("✅ requirements.txt updated")
        
    except Exception as e:
        print(f"❌ Failed to update requirements.txt: {e}")

def main():
    print("🚀 Enhanced Live Events Setup")
    print("=" * 40)
    
    # Install packages
    install_required_packages()
    
    # Setup database
    setup_database()
    
    # Update requirements
    update_requirements()
    
    print("\n" + "=" * 40)
    print("✅ Setup Complete!")
    print("\n📋 Files created:")
    print("- enhanced_live_events.py (WebSocket manager)")
    print("- live_events_frontend.py (JavaScript/CSS)")
    print("- live_events_integration.py (Integration guide)")
    print("- templates/live_events_enhanced.html (Enhanced template)")
    
    print("\n🔧 Next Steps:")
    print("1. Review live_events_integration.py")
    print("2. Update your app.py with the integration code")
    print("3. Test the WebSocket functionality")

if __name__ == "__main__":
    main()
