#!/usr/bin/env python3
"""
Test article access through browser simulation
"""

import requests
import sys

def test_with_session():
    """Test access with proper session handling"""
    session = requests.Session()
    
    # Set a proper User-Agent to pass browser detection
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        print("🔍 Testing landing page access...")
        response = session.get('http://localhost:5000/', timeout=10)
        print(f"Landing page: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Landing page accessible")
            
            # Check if we need to login
            if 'login' in response.text.lower() or 'sign in' in response.text.lower():
                print("📝 Authentication required - showing landing page")
            else:
                print("🏠 Dashboard accessible without login")
        
        print(f"\n🔍 Testing articles page access...")
        response = session.get('http://localhost:5000/articles', timeout=10)
        print(f"Articles page: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Articles page accessible")
            # Check content length to see if articles are loading
            content_length = len(response.text)
            print(f"📊 Page content size: {content_length:,} characters")
            
            if 'article' in response.text.lower():
                print("📰 Articles detected in page content")
            else:
                print("❓ No articles detected in page content")
        else:
            print(f"❌ Articles page blocked: HTTP {response.status_code}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_with_session()
