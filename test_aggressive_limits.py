#!/usr/bin/env python3
"""
Test script to force article limits and verify user-friendly messages
"""

import requests
import time
import threading

def test_aggressive_article_limits():
    """Test if article limits show user-friendly messages by making many rapid requests"""
    base_url = "http://127.0.0.1:5000"
    
    # Use a very obvious bot user agent
    headers = {
        'User-Agent': 'python-requests/2.25.1'
    }
    
    print("🧪 Testing article limit messages with aggressive requests...")
    print(f"📍 Making rapid requests to {base_url}/articles")
    
    # Make many rapid requests to trigger rate limits
    for i in range(100):  # Make 100 requests rapidly
        try:
            response = requests.get(f"{base_url}/articles", headers=headers, timeout=3)
            
            if response.status_code == 200:
                print(f"✅ Request {i+1}: Success")
            elif response.status_code == 429:
                data = response.json()
                print(f"\n🚫 Request {i+1}: Rate limited!")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                print(f"   Message: {data.get('message', 'No message')}")
                print(f"   Retry after: {data.get('retry_after', 'Unknown')} seconds")
                
                # Check if message is user-friendly
                message = data.get('message', '')
                if any(phrase in message.lower() for phrase in ['hourly limit', 'articles', 'fair access', 'upgrade']):
                    print("✅ User-friendly article limit message detected!")
                    print(f"   Message quality: {'⭐' * (4 if 'upgrade' in message.lower() else 3)}")
                else:
                    print("⚠️  Message might not be user-friendly enough")
                    print(f"   Actual message: {message}")
                break
            elif response.status_code == 403:
                data = response.json()
                print(f"\n🚫 Request {i+1}: Forbidden!")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                print(f"   Message: {data.get('message', 'No message')}")
                break
            else:
                print(f"❌ Request {i+1}: Unexpected status {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        print(f"   Response: {response.json()}")
                    except:
                        print(f"   Response text: {response.text}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i+1}: Network error - {e}")
            break
            
        # No delay - make requests as fast as possible to trigger limits
        if i % 10 == 9:  # Small pause every 10 requests to see intermediate results
            time.sleep(0.05)

def test_specific_article_endpoint():
    """Test accessing a specific article endpoint repeatedly"""
    base_url = "http://127.0.0.1:5000"
    
    headers = {
        'User-Agent': 'curl/7.68.0'  # Very obvious bot
    }
    
    print("\n🧪 Testing specific article endpoint limits...")
    print(f"📍 Making requests to {base_url}/article/1")
    
    for i in range(50):
        try:
            response = requests.get(f"{base_url}/article/1", headers=headers, timeout=3)
            
            if response.status_code == 200:
                print(f"✅ Article request {i+1}: Success")
            elif response.status_code == 429:
                data = response.json()
                print(f"\n🚫 Article request {i+1}: Rate limited!")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                print(f"   Message: {data.get('message', 'No message')}")
                
                message = data.get('message', '')
                if 'article' in message.lower():
                    print("✅ Article-specific limit message detected!")
                break
            elif response.status_code == 404:
                print(f"📄 Article request {i+1}: Article not found (expected)")
                # Continue testing even if article doesn't exist
            else:
                print(f"❌ Article request {i+1}: Status {response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Article request {i+1}: Network error - {e}")
            break

if __name__ == "__main__":
    test_aggressive_article_limits()
    test_specific_article_endpoint()
