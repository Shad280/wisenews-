#!/usr/bin/env python3
"""
Test script to verify user-friendly article limit messages
"""

import requests
import time

def test_article_limits():
    """Test if article limits show user-friendly messages"""
    base_url = "http://127.0.0.1:5000"
    
    # Use a bot-like user agent to trigger rate limits faster
    headers = {
        'User-Agent': 'test-bot/1.0'
    }
    
    print("🧪 Testing article limit messages...")
    print(f"📍 Making requests to {base_url}/articles")
    
    # Make multiple requests to potentially trigger article limits
    for i in range(25):  # Exceed the bot limit of 10 articles/hour
        try:
            response = requests.get(f"{base_url}/articles", headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Request {i+1}: Success")
            elif response.status_code == 429:
                data = response.json()
                print(f"🚫 Request {i+1}: Rate limited!")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                print(f"   Message: {data.get('message', 'No message')}")
                print(f"   Retry after: {data.get('retry_after', 'Unknown')} seconds")
                
                # Check if message is user-friendly
                message = data.get('message', '')
                if 'hourly limit' in message.lower() and 'articles' in message.lower():
                    print("✅ User-friendly article limit message detected!")
                else:
                    print("⚠️  Message might not be user-friendly enough")
                break
            else:
                print(f"❌ Request {i+1}: Unexpected status {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    print(f"   Response: {response.json()}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i+1}: Network error - {e}")
            break
            
        # Small delay between requests
        time.sleep(0.1)

if __name__ == "__main__":
    test_article_limits()
