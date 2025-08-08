#!/usr/bin/env python3
"""
Test actual Flask routes to identify 500 errors
"""

import requests
import time
import sys
from multiprocessing import Process
import os
import signal

def start_flask_app():
    """Start the Flask app in a separate process"""
    try:
        # Import and run the app
        import app
        app.app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask app failed to start: {e}")

def test_route(url, description):
    """Test a specific route"""
    try:
        print(f"🔍 Testing {description}: {url}")
        response = requests.get(url, timeout=10, allow_redirects=False)
        
        if response.status_code == 500:
            print(f"❌ 500 ERROR - {description}")
            print(f"   Response: {response.text[:200]}...")
            return False
        elif response.status_code == 200:
            print(f"✅ SUCCESS - {description}")
            return True
        elif response.status_code in [302, 301]:
            print(f"🔄 REDIRECT - {description} (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️ UNEXPECTED STATUS - {description} (Status: {response.status_code})")
            return True
    except requests.exceptions.ConnectionError:
        print(f"🔌 CONNECTION REFUSED - {description}")
        return False
    except Exception as e:
        print(f"❌ ERROR - {description}: {e}")
        return False

def test_post_route(url, data, description):
    """Test a POST route"""
    try:
        print(f"🔍 Testing {description}: {url}")
        response = requests.post(url, json=data, timeout=10, allow_redirects=False)
        
        if response.status_code == 500:
            print(f"❌ 500 ERROR - {description}")
            print(f"   Response: {response.text[:200]}...")
            return False
        elif response.status_code == 200:
            print(f"✅ SUCCESS - {description}")
            return True
        elif response.status_code in [302, 301, 401, 403]:
            print(f"🔄 EXPECTED STATUS - {description} (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️ UNEXPECTED STATUS - {description} (Status: {response.status_code})")
            return True
    except requests.exceptions.ConnectionError:
        print(f"🔌 CONNECTION REFUSED - {description}")
        return False
    except Exception as e:
        print(f"❌ ERROR - {description}: {e}")
        return False

def main():
    """Test the problematic routes"""
    print("🚀 STARTING ROUTE TESTING")
    print("=" * 50)
    
    # Start Flask app in background
    print("🔥 Starting Flask app...")
    flask_process = Process(target=start_flask_app)
    flask_process.start()
    
    # Wait for app to start
    print("⏳ Waiting for app to start...")
    time.sleep(5)
    
    base_url = "http://127.0.0.1:5555"
    
    # Test routes that user reported as having 500 errors
    test_routes = [
        # Subscription routes
        (f"{base_url}/subscription-plans", "Subscription Plans Page"),
        (f"{base_url}/api/subscription/plans", "Subscription Plans API"),
        
        # Chat routes
        (f"{base_url}/support/chat", "Support Chat Page"),
        (f"{base_url}/support/chat/guest", "Guest Chat Page"),
        (f"{base_url}/support", "Support Center"),
        
        # General routes to verify app is working
        (f"{base_url}/", "Home Page"),
        (f"{base_url}/live-feeds", "Live Feeds"),
    ]
    
    results = {}
    
    # Test GET routes
    for url, description in test_routes:
        results[description] = test_route(url, description)
        time.sleep(1)  # Brief pause between requests
    
    # Test POST routes
    post_tests = [
        (f"{base_url}/api/chat/send", {"message": "Hello, I need help"}, "Chat Send Message"),
        (f"{base_url}/api/subscription/purchase", {"plan": "standard"}, "Purchase Subscription"),
    ]
    
    for url, data, description in post_tests:
        results[description] = test_post_route(url, data, description)
        time.sleep(1)
    
    # Cleanup
    print("\n🛑 Stopping Flask app...")
    flask_process.terminate()
    flask_process.join(timeout=5)
    if flask_process.is_alive():
        flask_process.kill()
    
    # Results summary
    print("\n" + "=" * 50)
    print("📊 ROUTE TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} routes working")
    
    if passed != total:
        print("\n🚨 PROBLEMATIC ROUTES:")
        for test_name, passed_test in results.items():
            if not passed_test:
                print(f"   - {test_name}")

if __name__ == "__main__":
    main()
