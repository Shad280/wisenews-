"""
Test WiseNews API endpoints for brand-friendly messages
"""

import requests

def test_api_endpoints():
    print("🧪 Testing WiseNews API Endpoints for Brand Messages...")
    
    base_url = "http://127.0.0.1:5000"
    
    # Test with obvious bot user agent to trigger protection
    bot_headers = {
        'User-Agent': 'curl/7.68.0',
        'Accept': 'application/json'
    }
    
    endpoints_to_test = [
        '/api/articles',
        '/articles', 
        '/api/search'
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n🔍 Testing endpoint: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", headers=bot_headers, timeout=5)
            
            if response.status_code in [403, 503]:
                try:
                    data = response.json()
                    error_msg = data.get('error', 'No message')
                    message = data.get('message', 'No message')
                    brand = data.get('brand', 'No brand info')
                    
                    print(f"   📝 Status: {response.status_code}")
                    print(f"   🌟 Error: {error_msg}")
                    print(f"   💬 Message: {message}")
                    print(f"   🏷️ Brand: {brand}")
                    
                    if 'WiseNews' in error_msg or 'WiseNews' in message:
                        print(f"   ✅ WiseNews branding detected!")
                    else:
                        print(f"   ❌ Missing WiseNews branding")
                        
                except:
                    print(f"   📄 Raw response: {response.text}")
            else:
                print(f"   ✅ Status: {response.status_code} (endpoint accessible)")
                
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")

def test_browser_access():
    print("\n🌐 Testing Browser Access (Should Work)...")
    
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        response = requests.get("http://127.0.0.1:5000/articles", headers=browser_headers, timeout=5)
        print(f"   ✅ Browser access: {response.status_code}")
        if response.status_code == 200:
            print("   🌟 Browsers can access without issues!")
        
    except Exception as e:
        print(f"   ❌ Browser test error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_browser_access()
