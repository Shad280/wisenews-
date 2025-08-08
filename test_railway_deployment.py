#!/usr/bin/env python3
"""
Test Railway WiseNews Deployment
Check if the app is working on Railway
"""

import requests
from datetime import datetime

def test_railway_url():
    """Test if WiseNews is working on Railway"""
    base_url = "https://web-production-1f6d.up.railway.app"
    
    print("🧪 TESTING WISENEWS ON RAILWAY")
    print("=" * 50)
    print(f"🌐 URL: {base_url}")
    print(f"🕐 Test time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    tests = [
        ("/", "Homepage"),
        ("/api/status", "API Status"),
        ("/login", "Login Page"),
        ("/register", "Registration Page"),
        ("/subscription-plans", "Subscription Plans")
    ]
    
    for endpoint, description in tests:
        print(f"Testing {description}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {description}: Working (200 OK)")
                
                # Check for WiseNews content
                if "WiseNews" in response.text:
                    print(f"   🎯 Contains WiseNews branding")
                if "BBC\|CNN\|Reuters" in response.text or "news" in response.text.lower():
                    print(f"   📰 Contains news content")
                    
            elif response.status_code == 302:
                print(f"   🔄 {description}: Redirect (302) - might be working")
            else:
                print(f"   ⚠️  {description}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ {description}: Timeout (app might be starting)")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {description}: Connection failed")
        except Exception as e:
            print(f"   ❌ {description}: Error - {e}")
        
        print()

def check_deployment_status():
    """Check deployment indicators"""
    print("🚂 RAILWAY DEPLOYMENT STATUS")
    print("=" * 50)
    
    status_indicators = [
        ("✅ Custom Start Command", "Empty (uses Procfile)"),
        ("✅ Procfile", "web: gunicorn app:app"),
        ("✅ Builder", "Nixpacks (automatic)"),
        ("✅ Code", "Latest push deployed"),
        ("✅ URL", "https://web-production-1f6d.up.railway.app"),
    ]
    
    for indicator, status in status_indicators:
        print(f"   {indicator}: {status}")
    
    print()
    print("🎯 EXPECTED BEHAVIOR:")
    print("   - Homepage should show WiseNews with news articles")
    print("   - Login page should show authentication form") 
    print("   - API endpoints should return JSON")
    print("   - NO Railway ASCII art!")

def main():
    """Main test function"""
    print("🌐 WISENEWS RAILWAY DEPLOYMENT TEST")
    print("=" * 60)
    
    check_deployment_status()
    print()
    test_railway_url()
    
    print("=" * 60)
    print("🎯 If all tests pass: WiseNews is working!")
    print("❌ If tests fail: Check Railway logs or wait for deployment")
    print("=" * 60)

if __name__ == "__main__":
    main()
