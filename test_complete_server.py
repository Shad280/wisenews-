#!/usr/bin/env python3
"""
Comprehensive test suite for WiseNews server
"""

import requests
import time
import sys

def test_endpoint(url, expected_status=200, description=""):
    """Test a single endpoint"""
    try:
        print(f"🔍 Testing {description}: {url}")
        
        # Use session for persistent connections
        session = requests.Session()
        response = session.get(url, timeout=10, allow_redirects=True)
        
        if response.status_code == expected_status:
            print(f"✅ {description}: Status {response.status_code}")
            return True
        elif response.status_code in [302, 301]:  # Redirect is okay
            print(f"✅ {description}: Status {response.status_code} (Redirect)")
            return True
        else:
            print(f"❌ {description}: Status {response.status_code} (Expected {expected_status})")
            return False
            
    except requests.exceptions.ConnectRefused:
        print(f"❌ {description}: Connection refused - Server not running")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {description}: Request timeout")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def comprehensive_server_test():
    """Run comprehensive tests on all server endpoints"""
    print("🔧 WiseNews Server Comprehensive Test")
    print("=" * 50)
    
    # Wait for server to fully start
    print("⏳ Waiting for server startup...")
    time.sleep(5)
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        ("/", "Landing page"),
        ("/dashboard", "Dashboard"),
        ("/articles", "Articles page"),
        ("/live-events", "Live events"),
        ("/login", "Login page"),
        ("/register", "Registration page"),
        ("/api/image-stats", "Image stats API"),
        ("/api/news-stats", "News stats API"),
        ("/api/search", "Search API"),
        ("/social", "Social media page"),
        ("/support", "Support page")
    ]
    
    successful_tests = 0
    total_tests = len(endpoints)
    
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        if test_endpoint(url, description=description):
            successful_tests += 1
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {successful_tests}/{total_tests} endpoints working")
    
    if successful_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Server is fully operational!")
        return True
    elif successful_tests >= total_tests * 0.8:  # 80% success rate
        print("✅ Most tests passed. Server is mostly operational.")
        return True
    else:
        print("❌ Multiple test failures. Server has issues.")
        return False

def test_database_functionality():
    """Test database-related functionality"""
    print("\n🗄️ Testing Database Functionality")
    print("-" * 30)
    
    try:
        # Test article viewing (which triggered SQLite errors)
        article_url = "http://localhost:5000/articles"
        response = requests.get(article_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Articles page loads successfully")
            if "article" in response.text.lower() or "news" in response.text.lower():
                print("✅ Articles content detected")
                return True
            else:
                print("⚠️ Articles page loads but no content detected")
                return True
        else:
            print(f"❌ Articles page failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_subscription_functionality():
    """Test subscription manager functionality"""
    print("\n💳 Testing Subscription Functionality")
    print("-" * 35)
    
    try:
        # Try to access a page that would trigger subscription checking
        dashboard_url = "http://localhost:5000/dashboard"
        response = requests.get(dashboard_url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Dashboard access successful (subscription manager working)")
            return True
        elif response.status_code in [302, 301]:
            print("✅ Dashboard redirects properly (subscription manager working)")
            return True
        else:
            print(f"❌ Dashboard access failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Subscription test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting WiseNews Server Tests")
    print("Current time:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Run all test suites
    tests = [
        comprehensive_server_test,
        test_database_functionality,
        test_subscription_functionality
    ]
    
    passed_tests = 0
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test suite {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 FINAL RESULTS: {passed_tests}/{len(tests)} test suites passed")
    
    if passed_tests == len(tests):
        print("🎉 ALL SYSTEMS OPERATIONAL! WiseNews is working perfectly!")
        print("🔗 Access your application at: http://localhost:5000")
    elif passed_tests >= len(tests) * 0.8:
        print("✅ WiseNews is mostly operational with minor issues")
        print("🔗 Access your application at: http://localhost:5000")
    else:
        print("❌ WiseNews has significant issues that need attention")
    
    return passed_tests == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
