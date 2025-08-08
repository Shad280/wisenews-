#!/usr/bin/env python3
"""
Debug session expiration issue
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_session_issue():
    """Test the session expiration issue"""
    print("=== Debugging Session Expiration ===")
    
    # Create session with browser headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Test 1: Access login page
    print("Step 1: Accessing login page...")
    login_response = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_response.status_code}")
    
    if "session expired" in login_response.text.lower():
        print("❌ Session expired message found on login page")
    else:
        print("✅ Login page accessible without session expired message")
    
    # Test 2: Try to login
    print("\nStep 2: Attempting login...")
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123'
    }
    
    submit_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login submission status: {submit_response.status_code}")
    
    if submit_response.status_code == 302:
        print("✅ Login successful - redirecting")
        redirect_url = submit_response.headers.get('Location', '/dashboard')
        
        # Follow redirect
        print(f"\nStep 3: Following redirect to {redirect_url}...")
        dashboard_response = session.get(f"{BASE_URL}{redirect_url}")
        print(f"Dashboard status: {dashboard_response.status_code}")
        
        if "session expired" in dashboard_response.text.lower():
            print("❌ Session expired message found after login")
            print("This indicates the session validation is failing")
        else:
            print("✅ Dashboard accessible - login working correctly")
            
    else:
        print(f"❌ Login failed with status: {submit_response.status_code}")
        if "session expired" in submit_response.text.lower():
            print("❌ Session expired message found during login")
    
    # Test 3: Try admin login
    print("\n=== Testing Admin Login ===")
    admin_data = {
        'email': 'admin@wisenews.com',
        'password': 'WiseNews2025!'
    }
    
    admin_session = requests.Session()
    admin_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    admin_login = admin_session.post(f"{BASE_URL}/login", data=admin_data, allow_redirects=False)
    print(f"Admin login status: {admin_login.status_code}")
    
    if admin_login.status_code == 302:
        print("✅ Admin login successful")
        # Try to access dashboard
        admin_dashboard = admin_session.get(f"{BASE_URL}/dashboard")
        print(f"Admin dashboard status: {admin_dashboard.status_code}")
        
        if "session expired" in admin_dashboard.text.lower():
            print("❌ Admin session also expired after login")
        else:
            print("✅ Admin dashboard accessible")
    else:
        print(f"❌ Admin login failed: {admin_login.status_code}")

if __name__ == "__main__":
    test_session_issue()
