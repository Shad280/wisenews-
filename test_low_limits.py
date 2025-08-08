"""
Test script to trigger article limit messages with temporarily lowered limits
"""

import requests
import time
import json

def test_with_custom_limits():
    print("🧪 Testing with custom low limits...")
    
    base_url = "http://127.0.0.1:5000"
    headers = {
        'User-Agent': 'TestBot/1.0 (testing article limits)',  # Use a non-browser user agent
        'Accept': 'application/json'
    }
    
    # Make many requests quickly to trigger limits
    for i in range(1, 501):  # 500 requests should trigger even high limits
        try:
            response = requests.get(f"{base_url}/articles", headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Request {i}: Success")
            elif response.status_code == 429:
                # Rate limit hit - check if we get user-friendly message
                try:
                    data = response.json()
                    message = data.get('error', data.get('message', 'No message found'))
                    print(f"🚫 Request {i}: Rate Limited - Message: {message}")
                    
                    # Check if message is user-friendly
                    if any(phrase in message.lower() for phrase in [
                        'hourly limit', 'fair access', 'upgrade', 'try again', 'minutes'
                    ]):
                        print(f"✅ User-friendly message detected: {message}")
                    else:
                        print(f"❌ Technical error message: {message}")
                    
                    return  # Stop testing once we hit the limit
                except:
                    print(f"🚫 Request {i}: Rate Limited - Raw response: {response.text}")
                    return
            else:
                print(f"❌ Request {i}: Error {response.status_code}")
                
            # Small delay to simulate realistic usage
            if i % 10 == 0:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Request {i}: Exception - {str(e)}")
    
    print("🏁 Completed all requests without hitting rate limit")

if __name__ == "__main__":
    test_with_custom_limits()
