"""
Simple direct test for user-friendly article rate limit messages
"""

import requests
import time

def test_direct_article_limit():
    print("🧪 Testing direct article rate limit...")
    
    base_url = "http://127.0.0.1:5000"
    headers = {
        'User-Agent': 'ScraperBot/1.0 (testing article limits)',  # Non-browser user agent to bypass browser protection
        'Accept': 'application/json'
    }
    
    for i in range(1, 10):
        try:
            response = requests.get(f"{base_url}/articles", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Request {i}: Success - Got {len(data)} articles")
            elif response.status_code == 429:
                try:
                    data = response.json()
                    error_message = data.get('error', 'No message found')
                    print(f"🚫 Request {i}: Rate Limited")
                    print(f"📝 Message: {error_message}")
                    
                    if 'hourly limit' in error_message.lower() and 'articles' in error_message.lower():
                        print("✅ SUCCESS: User-friendly article limit message detected!")
                        print(f"📋 Full friendly message: {error_message}")
                        return True
                    else:
                        print(f"❌ Not the expected article message: {error_message}")
                        return False
                        
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    print(f"Raw response: {response.text}")
                    return False
            else:
                print(f"❌ Request {i}: Unexpected status {response.status_code}")
                print(f"Response: {response.text}")
            
            time.sleep(1)  # Wait 1 second between requests
                
        except Exception as e:
            print(f"❌ Request {i}: Exception - {str(e)}")
    
    print("🏁 Test completed without hitting article rate limit")
    return False

if __name__ == "__main__":
    success = test_direct_article_limit()
    if success:
        print("🎉 Test PASSED: User-friendly article messages are working!")
    else:
        print("❌ Test FAILED: User-friendly messages not detected")
