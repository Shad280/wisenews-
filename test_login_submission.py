#!/usr/bin/env python3
"""
Test script to debug login form submission
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_login_submission():
    """Test the actual login form submission"""
    print("=== Testing Login Form Submission ===")
    
    # Create session
    session = requests.Session()
    
    # Get login page first
    print("Step 1: Getting login page...")
    login_response = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("❌ Cannot access login page")
        return
    
    # Try to submit login form
    print("\nStep 2: Submitting login form...")
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123',
        'next': f"{BASE_URL}/dashboard"
    }
    
    print(f"Submitting login with data: {login_data}")
    
    # Submit login
    submit_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login submission status: {submit_response.status_code}")
    print(f"Login response headers: {dict(submit_response.headers)}")
    
    if submit_response.status_code == 302:
        print(f"Redirect location: {submit_response.headers.get('Location', 'No location')}")
        
        # Follow redirect
        print("\nStep 3: Following redirect...")
        redirect_response = session.get(submit_response.headers.get('Location', f"{BASE_URL}/dashboard"))
        print(f"Redirect status: {redirect_response.status_code}")
        print(f"Final URL: {redirect_response.url}")
        
        if redirect_response.status_code == 302:
            print("❌ Still being redirected - login failed")
        elif redirect_response.status_code == 200:
            print("✅ Login successful - reached dashboard")
        else:
            print(f"❌ Unexpected status: {redirect_response.status_code}")
            
    elif submit_response.status_code == 200:
        print("❌ Login form returned 200 - likely validation error")
        if 'Invalid email or password' in submit_response.text:
            print("Found error message in response")
    else:
        print(f"❌ Unexpected login response: {submit_response.status_code}")

if __name__ == "__main__":
    try:
        test_login_submission()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
