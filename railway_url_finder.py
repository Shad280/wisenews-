#!/usr/bin/env python3
"""
Railway URL Finder & Status Checker
Help find the correct Railway URL for WiseNews
"""

from datetime import datetime

def find_railway_urls():
    """Find possible Railway URLs for WiseNews"""
    print("🔍 FINDING YOUR ACTUAL RAILWAY URL")
    print("=" * 50)
    
    print("🎯 GITHUB REPO: https://github.com/Shad280/wisenews-.git")
    print()
    
    print("📋 POSSIBLE RAILWAY URLS:")
    print("Railway generates URLs based on your project name and ID.")
    print()
    
    # Common Railway URL patterns
    base_patterns = [
        "wisenews",
        "wisenews-production", 
        "news-scrapper",
        "news-scraper",
        "wise-news",
        "wisenews-app"
    ]
    
    for i, pattern in enumerate(base_patterns, 1):
        print(f"{i}. https://{pattern}.railway.app/")
        print(f"   OR: https://{pattern}-production.railway.app/")
        print()

def check_railway_dashboard_steps():
    """Steps to find actual URL in Railway dashboard"""
    print("🚂 HOW TO FIND YOUR ACTUAL RAILWAY URL:")
    print("=" * 50)
    
    steps = [
        "1. 🌐 Go to: https://railway.app/dashboard",
        "2. 🔐 Login with your Railway account",
        "3. 📁 Look for your WiseNews project (might be named differently)",
        "4. 📱 Click on your project",
        "5. ⚙️  Go to 'Settings' tab",
        "6. 🌐 Look for 'Domains' section",
        "7. 📋 Copy the Railway-provided URL",
        "8. ✅ That's your real WiseNews URL!"
    ]
    
    for step in steps:
        print(f"   {step}")

def why_showing_railway_ascii():
    """Explain why Railway ASCII art appears"""
    print("\n🎨 WHY YOU'RE SEEING RAILWAY ASCII ART:")
    print("=" * 50)
    
    reasons = [
        ("🔄 App Still Starting", "WiseNews is still initializing (most common)"),
        ("❌ App Failed to Start", "Check Railway logs for errors"),
        ("🌐 Wrong URL", "You might be on Railway's default page"),
        ("⏰ Deployment in Progress", "Railway is still building your app"),
        ("🛠️ Configuration Issue", "App not responding on correct port")
    ]
    
    for reason, description in reasons:
        print(f"   {reason:20} - {description}")

def current_deployment_status():
    """Show current deployment timeline"""
    print(f"\n⏰ CURRENT DEPLOYMENT STATUS:")
    print("=" * 50)
    
    print(f"🕐 Current time: {datetime.now().strftime('%H:%M:%S')}")
    print("📤 Last push: ~15 minutes ago (Procfile fix)")
    print("🔧 Fix applied: Corrected Procfile to 'web: gunicorn app:app'")
    print()
    
    print("📊 EXPECTED TIMELINE:")
    print("   ✅ Code pushed to Railway")
    print("   ✅ Railway building dependencies") 
    print("   🔄 Starting Gunicorn server")
    print("   🔄 Initializing SQLite database")
    print("   🔄 Loading news feeds")
    print("   ⏳ App should be ready soon!")

def next_actions():
    """What to do next"""
    print(f"\n🎯 WHAT TO DO NOW:")
    print("=" * 50)
    
    actions = [
        "1. 🚂 Find your real Railway URL using dashboard steps above",
        "2. ⏰ Wait 5-10 more minutes if app is still starting",
        "3. 🔄 Try hard refresh (Ctrl+F5) on the real URL",
        "4. 📱 Check Railway dashboard for deployment logs",
        "5. 🆘 If still ASCII art after 20 minutes, check logs"
    ]
    
    for action in actions:
        print(f"   {action}")
    
    print(f"\n💡 MOST LIKELY:")
    print("   You're either on the wrong URL or WiseNews is still starting.")
    print("   Check Railway dashboard for your actual project URL!")

def quick_test_commands():
    """Commands to test if deployment worked"""
    print(f"\n🧪 QUICK TESTS FOR YOUR REAL RAILWAY URL:")
    print("=" * 50)
    
    print("Once you find your real Railway URL, test these endpoints:")
    print()
    print("🏠 Homepage: https://your-real-url.railway.app/")
    print("   Should show: WiseNews homepage with news articles")
    print()
    print("📊 API Status: https://your-real-url.railway.app/api/status")
    print("   Should show: JSON with system status")
    print()
    print("🔐 Admin Login: https://your-real-url.railway.app/login")
    print("   Should show: Login form")
    print()
    print("❌ If you still see ASCII art on the real URL:")
    print("   → App failed to start, need to check Railway logs")

def main():
    """Main function"""
    print("🚂 RAILWAY ASCII ART TROUBLESHOOTER")
    print("=" * 60)
    print(f"🕐 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    find_railway_urls()
    check_railway_dashboard_steps()
    why_showing_railway_ascii()
    current_deployment_status()
    next_actions()
    quick_test_commands()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY: Find your real Railway URL in the dashboard!")
    print("The ASCII art means you're on Railway's default page.")
    print("=" * 60)

if __name__ == "__main__":
    main()
