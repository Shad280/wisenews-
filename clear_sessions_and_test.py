#!/usr/bin/env python3
"""
Clear all sessions and check session state
"""
import sqlite3
from datetime import datetime

def clear_all_sessions():
    """Clear all existing sessions to fix any corrupted session data"""
    print("=== Clearing All Sessions ===")
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check existing sessions
        cursor.execute('SELECT COUNT(*) FROM user_sessions')
        session_count = cursor.fetchone()[0]
        print(f"Found {session_count} existing sessions")
        
        if session_count > 0:
            # Show existing sessions
            cursor.execute('''
                SELECT us.id, us.user_id, u.email, us.created_at, us.expires_at, us.is_active
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                ORDER BY us.created_at DESC
            ''')
            sessions = cursor.fetchall()
            
            print("\nExisting sessions:")
            for session in sessions:
                sess_id, user_id, email, created, expires, is_active = session
                status = "ACTIVE" if is_active else "INACTIVE"
                print(f"  Session {sess_id}: User {user_id} ({email}) - {status}")
                print(f"    Created: {created}")
                print(f"    Expires: {expires}")
            
            # Clear all sessions
            cursor.execute('DELETE FROM user_sessions')
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"\n✅ Cleared {deleted_count} sessions")
        else:
            print("No sessions to clear")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing sessions: {e}")
        return False

def test_fresh_login():
    """Test login with completely fresh session"""
    print("\n=== Testing Fresh Login ===")
    
    import requests
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    BASE_URL = "http://127.0.0.1:5000"
    
    # Test login
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("✅ Login successful")
        
        # Check if session was created in database
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE is_active = 1')
        active_sessions = cursor.fetchone()[0]
        print(f"Active sessions in database: {active_sessions}")
        conn.close()
        
        # Try to access dashboard
        dashboard_response = session.get(f"{BASE_URL}/dashboard")
        print(f"Dashboard access: {dashboard_response.status_code}")
        
        if "session expired" in dashboard_response.text.lower():
            print("❌ Still getting session expired message")
            # Save the response to check what's happening
            with open('dashboard_response.html', 'w', encoding='utf-8') as f:
                f.write(dashboard_response.text)
            print("Dashboard response saved to dashboard_response.html")
        else:
            print("✅ Dashboard accessible without session expired message")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    # Clear all sessions
    if clear_all_sessions():
        # Test fresh login
        test_fresh_login()
    else:
        print("Failed to clear sessions")
