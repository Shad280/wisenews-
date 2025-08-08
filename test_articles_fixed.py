#!/usr/bin/env python3
"""
Test Articles Page Access After Fixes
"""
import requests
import sys

def test_articles_page():
    """Test the articles page after applying the fixes"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing WiseNews Articles Page After Fixes...")
    print("=" * 60)
    
    try:
        # Test articles page
        print("📄 Testing /articles page...")
        response = requests.get(f"{base_url}/articles", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: Articles page is working!")
            # Check if it contains expected content
            content = response.text.lower()
            if 'articles' in content or 'news' in content:
                print("   ✅ Page contains expected content")
            else:
                print("   ⚠️  Page loaded but may not have expected content")
        elif response.status_code == 403:
            print("   ⚠️  FORBIDDEN: Articles page requires authentication")
        elif response.status_code == 500:
            print("   ❌ ERROR: Still getting 500 server error")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   ❓ UNEXPECTED: Got status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Cannot connect to server (is it running?)")
    except requests.exceptions.Timeout:
        print("   ❌ ERROR: Request timed out")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_articles_page()
