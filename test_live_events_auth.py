import requests
import sqlite3
from datetime import datetime, timedelta

def test_live_events_backend():
    """Test the live events database directly"""
    print("🔍 Testing Live Events Backend...")
    
    try:
        # Connect to database and check current live events
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check all events with status='live'
        cursor.execute("""
            SELECT id, event_name, status, category, created_at, last_updated
            FROM live_events 
            WHERE status = 'live'
            ORDER BY last_updated DESC
        """)
        
        live_events = cursor.fetchall()
        print(f"✅ Found {len(live_events)} live events in database:")
        
        for event in live_events:
            event_id, name, status, category, created, updated = event
            print(f"   📍 Event {event_id}: {name} ({category}) - Updated: {updated}")
            
        # Test time filtering (events within last 2 hours)
        two_hours_ago = datetime.now() - timedelta(hours=2)
        cursor.execute("""
            SELECT id, event_name, status, category, created_at, last_updated
            FROM live_events 
            WHERE status = 'live' 
            AND last_updated >= ?
            ORDER BY last_updated DESC
        """, (two_hours_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        
        recent_events = cursor.fetchall()
        print(f"\n⏰ Events within last 2 hours: {len(recent_events)}")
        
        for event in recent_events:
            event_id, name, status, category, created, updated = event
            print(f"   🔥 Event {event_id}: {name} ({category}) - Updated: {updated}")
            
        conn.close()
        
        # Test if we can access the endpoint without auth
        print(f"\n🌐 Testing live events endpoint...")
        try:
            response = requests.get('http://127.0.0.1:5000/live-events', timeout=5)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 302:
                print("   ⚠️ Redirected to login - authentication required")
                if 'login' in response.headers.get('Location', ''):
                    print("   🔒 Live events page requires user authentication")
            elif response.status_code == 200:
                print("   ✅ Live events page accessible")
                if 'live' in response.text.lower():
                    print("   📱 Page contains live events content")
                else:
                    print("   ⚠️ Page doesn't appear to show live events")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
            
        return len(recent_events) > 0
        
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def check_user_setup():
    """Check if there are any test users in the database"""
    print("\n👤 Checking user setup...")
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check if users table exists and has any users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("SELECT username, email FROM users LIMIT 5")
            users = cursor.fetchall()
            print(f"   📊 Found {len(users)} users in database")
            if users:
                for username, email in users:
                    print(f"   👤 User: {username} ({email})")
        else:
            print("   ⚠️ No users table found")
            
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error checking users: {e}")

if __name__ == "__main__":
    print("🚀 WiseNews Live Events Authentication Test\n")
    
    # Test backend functionality
    has_live_events = test_live_events_backend()
    
    # Check user setup
    check_user_setup()
    
    print(f"\n📊 Summary:")
    print(f"   {'✅' if has_live_events else '❌'} Live events backend: {'Working' if has_live_events else 'No recent events'}")
    print(f"   🔒 Authentication: Required for /live-events endpoint")
    print(f"   💡 Recommendation: Test with authenticated session or check auth requirements")
