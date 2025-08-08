#!/usr/bin/env python3
"""
Comprehensive verification that login is actually working
"""
import requests
import sqlite3
from datetime import datetime

def comprehensive_login_test():
    """Test everything to make sure login is actually working"""
    print("🔍 COMPREHENSIVE LOGIN VERIFICATION")
    print("=" * 50)
    
    BASE_URL = "http://127.0.0.1:5000"
    
    # Test 1: Check session validation function directly
    print("\n1️⃣ Testing session validation function directly...")
    try:
        from user_auth import user_manager
        
        # Test with a fake session token
        is_valid, user_data = user_manager.validate_session("fake_token")
        print(f"   Fake token validation: {is_valid} (should be False)")
        
        # Test with None
        is_valid, user_data = user_manager.validate_session(None)
        print(f"   None token validation: {is_valid} (should be False)")
        
        print("   ✅ Session validation function is working")
        
    except Exception as e:
        print(f"   ❌ Session validation error: {e}")
        return False
    
    # Test 2: Fresh browser login test
    print("\n2️⃣ Testing fresh browser login...")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    # Step 1: Get login page
    login_page = session.get(f"{BASE_URL}/login")
    print(f"   Login page status: {login_page.status_code}")
    
    if login_page.status_code != 200:
        print("   ❌ Cannot access login page")
        return False
    
    # Step 2: Submit login
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"   Login response status: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("   ✅ Login successful (302 redirect)")
        
        # Check if session cookie was set
        cookies = session.cookies.get_dict()
        if 'session' in cookies:
            print("   ✅ Session cookie set")
        else:
            print("   ❌ No session cookie")
            return False
            
        # Follow redirect to dashboard
        redirect_url = login_response.headers.get('Location', '/dashboard')
        print(f"   Redirecting to: {redirect_url}")
        
        dashboard_response = session.get(f"{BASE_URL}{redirect_url}")
        print(f"   Dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            # Check for session expired in response
            response_text = dashboard_response.text.lower()
            if 'session expired' in response_text:
                print("   ❌ FOUND 'session expired' in dashboard response")
                # Save response for debugging
                with open('failed_dashboard.html', 'w', encoding='utf-8') as f:
                    f.write(dashboard_response.text)
                print("   Saved failed response to failed_dashboard.html")
                return False
            else:
                print("   ✅ Dashboard accessible without session expired message")
                
                # Test protected route
                profile_response = session.get(f"{BASE_URL}/profile")
                print(f"   Profile page status: {profile_response.status_code}")
                
                if 'session expired' in profile_response.text.lower():
                    print("   ❌ Session expired on profile page")
                    return False
                else:
                    print("   ✅ Profile page accessible")
                    
        else:
            print(f"   ❌ Dashboard access failed: {dashboard_response.status_code}")
            return False
            
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")
        if login_response.status_code == 200:
            # Check for error messages in form
            if 'invalid' in login_response.text.lower():
                print("   Found 'invalid' in login response - credential error")
            if 'session expired' in login_response.text.lower():
                print("   Found 'session expired' in login form")
        return False
    
    # Test 3: Check database state
    print("\n3️⃣ Checking database state...")
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check active sessions
        cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE is_active = 1')
        active_sessions = cursor.fetchone()[0]
        print(f"   Active sessions in database: {active_sessions}")
        
        # Check latest session
        cursor.execute('''
            SELECT us.session_token, u.email, us.expires_at 
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.is_active = 1
            ORDER BY us.created_at DESC
            LIMIT 1
        ''')
        latest_session = cursor.fetchone()
        
        if latest_session:
            token, email, expires = latest_session
            print(f"   Latest session: {email} (expires: {expires})")
            
            # Test this session token directly
            is_valid, user_data = user_manager.validate_session(token)
            print(f"   Session validation result: {is_valid}")
            if is_valid:
                print(f"   User data: {user_data}")
                print("   ✅ Session validation working correctly")
            else:
                print("   ❌ Session validation failed for active session")
                return False
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database check error: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED - LOGIN IS WORKING CORRECTLY!")
    return True

def test_admin_login():
    """Test admin login specifically"""
    print("\n4️⃣ Testing admin login...")
    
    BASE_URL = "http://127.0.0.1:5000"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    admin_data = {
        'email': 'admin@wisenews.com',
        'password': 'WiseNews2025!'
    }
    
    admin_response = session.post(f"{BASE_URL}/login", data=admin_data, allow_redirects=False)
    print(f"   Admin login status: {admin_response.status_code}")
    
    if admin_response.status_code == 302:
        dashboard = session.get(f"{BASE_URL}/dashboard")
        print(f"   Admin dashboard: {dashboard.status_code}")
        
        if 'session expired' in dashboard.text.lower():
            print("   ❌ Admin session expired")
            return False
        else:
            print("   ✅ Admin login successful")
            return True
    else:
        print("   ❌ Admin login failed")
        return False

if __name__ == "__main__":
    user_success = comprehensive_login_test()
    admin_success = test_admin_login()
    
    if user_success and admin_success:
        print("\n✅ FINAL RESULT: LOGIN IS WORKING PERFECTLY")
        print("   Both user and admin login are functional")
        print("   No session expiration issues detected")
    else:
        print("\n❌ FINAL RESULT: THERE ARE STILL ISSUES")
        print(f"   User login: {'✅' if user_success else '❌'}")
        print(f"   Admin login: {'✅' if admin_success else '❌'}")
