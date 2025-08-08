#!/usr/bin/env python3
"""
Quick debug test for the specific 500 error features mentioned by user
"""
import requests
import json

def test_app_features():
    """Test the specific features that are causing 500 errors"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 TESTING SPECIFIC 500 ERROR FEATURES")
    print("=" * 60)
    
    # Test cases for the specific problematic features
    test_cases = [
        ("Start Chat", "/chat"),
        ("My Subscription", "/subscription"),
        ("Report Issue", "/support"),
        ("API Keys", "/api-keys"),
        ("Main Dashboard", "/"),
        ("Login Page", "/login"),
        ("Articles Page", "/articles")
    ]
    
    session = requests.Session()
    
    for feature_name, endpoint in test_cases:
        try:
            print(f"\n🔍 Testing: {feature_name} ({endpoint})")
            
            response = session.get(f"{base_url}{endpoint}", 
                                 timeout=10,
                                 allow_redirects=False)
            
            status_color = "🟢" if response.status_code < 400 else "🔴"
            print(f"   {status_color} Status: {response.status_code}")
            
            if response.status_code == 302:
                redirect_location = response.headers.get('Location', 'Unknown')
                print(f"   ↪️  Redirect to: {redirect_location}")
            elif response.status_code == 500:
                print(f"   ❌ 500 ERROR CONFIRMED!")
                print(f"   📝 Content preview: {response.text[:200]}...")
            elif response.status_code == 200:
                print(f"   ✅ SUCCESS - Page loads correctly")
                if 'text/html' in response.headers.get('content-type', ''):
                    content_preview = response.text[:100].replace('\n', ' ')
                    print(f"   📄 Content: {content_preview}...")
            
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR - App not running on {base_url}")
            break
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT - Request took too long")
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    print(f"\n📋 SUMMARY:")
    print(f"   App running on: {base_url}")
    print(f"   Test completed at: {requests.utils.datetime.datetime.now()}")

if __name__ == "__main__":
    test_app_features()
