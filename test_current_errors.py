#!/usr/bin/env python3
"""
Test the specific routes that were causing 500 errors
"""

import requests
import time

def test_specific_routes():
    """Test the routes you mentioned"""
    print("🧪 TESTING SPECIFIC ROUTES THAT WERE CAUSING ERRORS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    
    # Give the app time to fully start
    print("Waiting for app to start...")
    time.sleep(3)
    
    routes_to_test = [
        ("/support/chat", "Start Chat"),
        ("/support", "Report an Issue"),
        ("/my-subscription", "My Subscription"),
        ("/subscription-plans", "Subscription Plans"),
        ("/support/chat/guest", "Guest Chat"),
        ("/api/chat/send", "Chat API")
    ]
    
    session = requests.Session()
    results = {}
    
    print("\nTesting routes:")
    print("-" * 40)
    
    for route, description in routes_to_test:
        try:
            response = session.get(f"{base_url}{route}", timeout=5)
            status_code = response.status_code
            
            if status_code == 500:
                print(f"❌ {description} ({route}): 500 ERROR - STILL BROKEN")
                # Try to get error details
                try:
                    error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    print(f"    Error details: {error_text}")
                except:
                    print(f"    Error details: Could not read response")
                results[route] = "❌ 500 Error"
                
            elif status_code in [200, 201]:
                print(f"✅ {description} ({route}): SUCCESS (Status {status_code})")
                results[route] = "✅ Working"
                
            elif status_code in [302, 301, 303, 307, 308]:
                print(f"↗️ {description} ({route}): REDIRECT (Status {status_code}) - Normal for protected routes")
                results[route] = "↗️ Redirect"
                
            elif status_code == 401:
                print(f"🔐 {description} ({route}): UNAUTHORIZED (Status {status_code}) - Need login")
                results[route] = "🔐 Auth required"
                
            elif status_code == 403:
                print(f"🚫 {description} ({route}): FORBIDDEN (Status {status_code})")
                results[route] = "🚫 Forbidden"
                
            elif status_code == 404:
                print(f"🔍 {description} ({route}): NOT FOUND (Status {status_code})")
                results[route] = "🔍 Not found"
                
            else:
                print(f"⚠️ {description} ({route}): Status {status_code}")
                results[route] = f"⚠️ Status {status_code}"
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 {description} ({route}): CONNECTION REFUSED - App may not be running")
            results[route] = "🔌 Connection refused"
            
        except requests.exceptions.Timeout:
            print(f"⏰ {description} ({route}): TIMEOUT")
            results[route] = "⏰ Timeout"
            
        except Exception as e:
            print(f"❌ {description} ({route}): ERROR - {e}")
            results[route] = f"❌ {e}"
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("-" * 30)
    
    error_500_count = sum(1 for r in results.values() if "500 Error" in r)
    working_count = sum(1 for r in results.values() if "Working" in r)
    redirect_count = sum(1 for r in results.values() if "Redirect" in r)
    connection_issues = sum(1 for r in results.values() if "Connection" in r or "Timeout" in r)
    
    print(f"✅ Working routes: {working_count}")
    print(f"↗️ Redirecting routes: {redirect_count}")
    print(f"❌ 500 Errors: {error_500_count}")
    print(f"🔌 Connection issues: {connection_issues}")
    
    if error_500_count > 0:
        print(f"\n🚨 STILL HAVE {error_500_count} ROUTES WITH 500 ERRORS!")
        print("Routes with 500 errors:")
        for route, status in results.items():
            if "500 Error" in status:
                print(f"   - {route}")
    elif connection_issues > 0:
        print(f"\n🔌 App may not be running. Start with: python app.py")
    else:
        print(f"\n🎉 NO 500 ERRORS FOUND! All routes working correctly!")
        
    return results

if __name__ == "__main__":
    test_specific_routes()
