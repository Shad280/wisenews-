#!/usr/bin/env python3
"""
Test script to debug login form submission with full response details
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_login_detailed():
    """Test the actual login form submission with detailed response"""
    print("=== Detailed Login Test ===")
    
    # Create session
    session = requests.Session()
    
    # Get login page first
    print("Step 1: Getting login page...")
    login_response = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_response.status_code}")
    
    # Try to submit login form
    print("\nStep 2: Submitting login form...")
    login_data = {
        'email': 'stamound1@outlook.com',
        'password': 'admin123'
    }
    
    print(f"Submitting login with data: {login_data}")
    
    # Submit login
    submit_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login submission status: {submit_response.status_code}")
    print(f"Login response headers: {dict(submit_response.headers)}")
    print(f"Login response content: {submit_response.text[:500]}")
    
    # Also test without next parameter
    print("\n=== Testing without 'next' parameter ===")
    submit_response2 = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login submission status: {submit_response2.status_code}")
    print(f"Login response content: {submit_response2.text[:500]}")

if __name__ == "__main__":
    try:
        test_login_detailed()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
