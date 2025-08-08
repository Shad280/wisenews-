"""
Test script specifically for article endpoint limits
"""

import requests
import time
import json

def test_article_endpoint():
    print("🧪 Testing article endpoint rate limits...")
    
    base_url = "http://127.0.0.1:5000"
    headers = {
        'User-Agent': 'TestBot/1.0 (testing article limits)',  # Use a non-browser user agent
        'Accept': 'application/json'
    }
    
    # Test article endpoint specifically
    for i in range(1, 10):  # Make requests until we hit the 5 article limit
        try:
            response = requests.get(f"{base_url}/articles", headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Article request {i}: Success")
            elif response.status_code == 429:
                # Rate limit hit - check if we get user-friendly message
                try:
                    data = response.json()
                    message = data.get('error', 'No message found')
                    print(f"🚫 Article request {i}: Rate Limited")
                    print(f"📝 Error message: {message}")
                    
                    # Check if message is user-friendly for articles
                    if any(phrase in message.lower() for phrase in [
                        'hourly limit', 'fair access', 'upgrade', 'try again', 'minutes', 'articles'
                    ]):
                        print(f"✅ User-friendly article message detected!")
                        print(f"📋 Full message: {message}")
                    else:
                        print(f"❌ Technical error message: {message}")
                    
                    return  # Stop testing once we hit the limit
                except Exception as e:
                    print(f"🚫 Article request {i}: Rate Limited - Raw response: {response.text}")
                    print(f"Error parsing JSON: {e}")
                    return
            else:
                print(f"❌ Article request {i}: Error {response.status_code} - {response.text}")
                
            # Small delay between requests
            time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Article request {i}: Exception - {str(e)}")
    
    print("🏁 Completed all requests without hitting article rate limit")

if __name__ == "__main__":
    test_article_endpoint()
