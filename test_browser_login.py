#!/usr/bin/env python3
"""
Test login with browser user agent to bypass protection
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_login_with_browser_agent():
    """Test login with browser user agent"""
    print("=== Testing Login with Browser User Agent ===")
    
    # Create session with browser-like headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Get login page first
    print("Step 1: Getting login page...")
    login_response = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("❌ Cannot access login page")
        return
    
    # Try to submit login form
    print("\nStep 2: Submitting login form with browser headers...")
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123'
    }
    
    print(f"Submitting login with data: {login_data}")
    
    # Submit login
    submit_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login submission status: {submit_response.status_code}")
    print(f"Login response headers: {dict(submit_response.headers)}")
    
    if submit_response.status_code == 302:
        redirect_location = submit_response.headers.get('Location', 'No location')
        print(f"✅ Login successful! Redirect to: {redirect_location}")
        
        # Follow redirect to see if we can access dashboard
        print("\nStep 3: Following redirect...")
        dashboard_response = session.get(redirect_location if redirect_location.startswith('http') else f"{BASE_URL}{redirect_location}")
        print(f"Dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("✅ Successfully accessed dashboard!")
        else:
            print(f"❌ Dashboard access failed: {dashboard_response.status_code}")
            
    elif submit_response.status_code == 200:
        print("❌ Login form returned 200 - check for validation errors")
        if 'Invalid email or password' in submit_response.text:
            print("Found 'Invalid email or password' error")
        elif 'required' in submit_response.text.lower():
            print("Found validation error in response")
        else:
            print("Login page returned, but no obvious error message found")
    else:
        print(f"❌ Unexpected login response: {submit_response.status_code}")
        print(f"Response content: {submit_response.text[:500]}")

if __name__ == "__main__":
    try:
        test_login_with_browser_agent()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
