#!/usr/bin/env python3
"""
Test Server Error Resolution
"""
import requests
import sys

def test_server_endpoints():
    """Test various server endpoints for errors"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing WiseNews Server After Advanced Fixes...")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        ("/", "Landing page"),
        ("/articles", "Articles page"),
        ("/dashboard", "Dashboard"),
        ("/live-events", "Live events"),
        ("/login", "Login page")
    ]
    
    errors_found = 0
    
    for endpoint, description in endpoints:
        try:
            print(f"📡 Testing {description}: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: {response.status_code} - Content: {len(response.content)} bytes")
            elif response.status_code in [302, 403]:
                print(f"   ℹ️  REDIRECT/AUTH: {response.status_code} (expected for auth-protected pages)")
            elif response.status_code == 500:
                print(f"   ❌ SERVER ERROR: {response.status_code}")
                errors_found += 1
                # Show error details
                if response.text:
                    error_preview = response.text[:200].replace('\n', ' ')
                    print(f"   💥 Error preview: {error_preview}...")
            else:
                print(f"   ⚠️  UNEXPECTED: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR: Server not running?")
            errors_found += 1
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT: Server not responding")
            errors_found += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            errors_found += 1
    
    print("\n" + "=" * 60)
    if errors_found == 0:
        print("🎉 SUCCESS: No server errors detected!")
        print("✅ All fixes appear to be working correctly")
    else:
        print(f"⚠️  ISSUES FOUND: {errors_found} endpoints still have problems")
        print("💡 Check server logs for detailed error information")
    
    return errors_found == 0

if __name__ == "__main__":
    success = test_server_endpoints()
    sys.exit(0 if success else 1)
