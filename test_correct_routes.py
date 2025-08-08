#!/usr/bin/env python3
"""
Fixed test for the specific features with CORRECT URLs
"""
import requests
from datetime import datetime

def test_correct_routes():
    """Test the specific features with correct URLs"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 TESTING CORRECT ROUTE URLS")
    print("=" * 60)
    
    # CORRECT URLs based on actual route inspection
    test_cases = [
        ("Start Chat", "/support/chat"),              # Blueprint route
        ("Support Chat Guest", "/support/chat/guest"), # Blueprint route  
        ("My Subscription", "/subscription-plans"),    # Main app route
        ("Report Issue (Support)", "/support"),       # Blueprint route
        ("API Keys (Admin)", "/admin/api-keys"),      # Admin route
        ("Main Dashboard", "/"),                       # Main route
        ("Login Page", "/login"),                      # Working route
        ("Articles Page", "/articles"),                # Working route
        ("Support FAQ", "/support/faq"),              # Blueprint route
        ("Support Contact", "/support/contact"),      # Blueprint route
        ("User Profile", "/profile"),                  # Main route
        ("Analytics", "/analytics"),                   # Main route
    ]
    
    session = requests.Session()
    
    working_routes = []
    error_routes = []
    auth_required_routes = []
    
    for feature_name, endpoint in test_cases:
        try:
            print(f"\n🔍 Testing: {feature_name} ({endpoint})")
            
            response = session.get(f"{base_url}{endpoint}", 
                                 timeout=10,
                                 allow_redirects=False)
            
            if response.status_code == 200:
                status_color = "🟢"
                working_routes.append((feature_name, endpoint))
                print(f"   {status_color} Status: {response.status_code} ✅ SUCCESS")
            elif response.status_code == 302:
                status_color = "🟡"
                redirect_location = response.headers.get('Location', 'Unknown')
                auth_required_routes.append((feature_name, endpoint, redirect_location))
                print(f"   {status_color} Status: {response.status_code} ↪️  Redirect to: {redirect_location}")
            elif response.status_code == 403:
                status_color = "🔴"
                auth_required_routes.append((feature_name, endpoint, "403 Forbidden"))
                print(f"   {status_color} Status: {response.status_code} 🚫 FORBIDDEN (Need login)")
            elif response.status_code == 404:
                status_color = "🔴"
                error_routes.append((feature_name, endpoint, "404 Not Found"))
                print(f"   {status_color} Status: {response.status_code} ❌ NOT FOUND")
            elif response.status_code == 500:
                status_color = "💥"
                error_routes.append((feature_name, endpoint, "500 Server Error"))
                print(f"   {status_color} Status: {response.status_code} 💥 SERVER ERROR!")
                print(f"   📝 Error preview: {response.text[:200]}...")
            else:
                status_color = "❓"
                print(f"   {status_color} Status: {response.status_code} ❓ UNKNOWN")
            
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR - App not running on {base_url}")
            break
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT - Request took too long")
            error_routes.append((feature_name, endpoint, "Timeout"))
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            error_routes.append((feature_name, endpoint, str(e)))
    
    print(f"\n" + "=" * 60)
    print(f"📋 FINAL SUMMARY:")
    print(f"   🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   🌐 App running on: {base_url}")
    
    print(f"\n🟢 WORKING ROUTES ({len(working_routes)}):")
    for feature, route in working_routes:
        print(f"   ✅ {feature}: {route}")
    
    print(f"\n🟡 AUTH REQUIRED ROUTES ({len(auth_required_routes)}):")
    for feature, route, info in auth_required_routes:
        print(f"   🔐 {feature}: {route} → {info}")
    
    print(f"\n🔴 ERROR ROUTES ({len(error_routes)}):")
    for feature, route, error in error_routes:
        print(f"   ❌ {feature}: {route} → {error}")
    
    if len(error_routes) == 0:
        print(f"\n🎉 SUCCESS: No 500 errors found! Issues are authentication-related.")
        print(f"💡 SOLUTION: You need to login first to access protected features.")
    else:
        print(f"\n⚠️  Found {len(error_routes)} routes with real errors that need fixing.")

if __name__ == "__main__":
    test_correct_routes()
