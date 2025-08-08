#!/usr/bin/env python3
"""
Railway 502 Error Diagnostics
Help identify why WiseNews is getting 502 errors
"""

from datetime import datetime

def analyze_502_error():
    """Analyze the 502 error and provide solutions"""
    print("🚨 RAILWAY 502 ERROR ANALYSIS")
    print("=" * 50)
    print(f"🕐 Analysis time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    print("❌ CURRENT STATUS: HTTP 502 Bad Gateway")
    print("🔍 MEANING: Railway can't connect to your app")
    print()
    
    print("🎯 MOST LIKELY CAUSES:")
    causes = [
        ("App startup failure", "Python import errors, syntax issues"),
        ("Port binding issues", "App not listening on correct port"),
        ("Memory/resource limits", "App using too much memory"),
        ("Database initialization", "SQLite setup problems"),
        ("Dependency issues", "Missing packages or version conflicts"),
        ("Gunicorn configuration", "WSGI server startup problems")
    ]
    
    for cause, description in causes:
        print(f"   • {cause}: {description}")
    print()

def railway_troubleshooting_steps():
    """Provide step-by-step troubleshooting"""
    print("🛠️ RAILWAY TROUBLESHOOTING STEPS:")
    print("=" * 50)
    
    steps = [
        ("1. Check Railway Logs", [
            "Install Railway CLI: npm install -g @railway/cli",
            "Login: railway login", 
            "View logs: railway logs",
            "Look for Python errors, import failures, or port issues"
        ]),
        
        ("2. Verify App Configuration", [
            "Custom Start Command: Empty ✅",
            "Procfile content: web: gunicorn app:app ✅",
            "Builder: Nixpacks ✅",
            "Check if app.py has syntax errors"
        ]),
        
        ("3. Test Local Startup", [
            "Run: python app.py locally",
            "Check for import errors",
            "Verify database initialization",
            "Test if app starts without errors"
        ]),
        
        ("4. Check Resource Usage", [
            "Memory limit: 8GB (should be enough)",
            "CPU limit: 8 vCPU (should be enough)",
            "Check if app uses too much memory on startup"
        ])
    ]
    
    for step_title, step_items in steps:
        print(f"\n{step_title}:")
        for item in step_items:
            print(f"   • {item}")

def potential_fixes():
    """Provide potential fixes for common issues"""
    print("\n🔧 POTENTIAL FIXES:")
    print("=" * 50)
    
    fixes = [
        ("Memory Optimization", [
            "Reduce news sources in app.py",
            "Disable background news fetching temporarily",
            "Simplify database initialization"
        ]),
        
        ("Port Configuration", [
            "Verify app uses: port = int(os.environ.get('PORT', 5000))",
            "Ensure app.run(host='0.0.0.0', port=port)",
            "Check gunicorn uses $PORT environment variable"
        ]),
        
        ("Dependency Issues", [
            "Update requirements.txt with exact versions",
            "Test: pip install -r requirements.txt locally",
            "Remove unnecessary packages"
        ]),
        
        ("Quick Test Fix", [
            "Create minimal test app to verify Railway works",
            "Then gradually add WiseNews features",
            "Identify which component causes the 502"
        ])
    ]
    
    for fix_category, fix_items in fixes:
        print(f"\n{fix_category}:")
        for item in fix_items:
            print(f"   • {item}")

def immediate_actions():
    """Immediate actions to take"""
    print("\n⚡ IMMEDIATE ACTIONS:")
    print("=" * 50)
    
    actions = [
        "1. 📋 Install Railway CLI and check logs",
        "2. 🧪 Test app startup locally: python app.py",
        "3. 🔍 Look for specific error messages in Railway logs",
        "4. 🔄 Try force redeploy if no obvious errors",
        "5. 💾 Consider creating minimal test version first"
    ]
    
    for action in actions:
        print(f"   {action}")
    
    print("\n💡 NEXT STEPS:")
    print("   Railway logs will show the exact error causing 502")
    print("   Without logs, we're troubleshooting blind")
    print("   Install Railway CLI to see what's actually failing")

def railway_cli_setup():
    """Railway CLI setup instructions"""
    print("\n📱 RAILWAY CLI SETUP:")
    print("=" * 50)
    
    print("If you have Node.js installed:")
    print("   npm install -g @railway/cli")
    print("   railway login")
    print("   railway logs")
    print()
    print("If you don't have Node.js:")
    print("   1. Download from: https://nodejs.org/")
    print("   2. Install Node.js")
    print("   3. Run the npm commands above")
    print()
    print("Alternative: Check Railway dashboard logs:")
    print("   1. Go to Railway dashboard")
    print("   2. Click your project")
    print("   3. Check 'Deployments' tab for error details")

def main():
    """Main diagnostic function"""
    print("🚨 RAILWAY 502 ERROR TROUBLESHOOTING GUIDE")
    print("=" * 60)
    
    analyze_502_error()
    railway_troubleshooting_steps()
    potential_fixes()
    immediate_actions()
    railway_cli_setup()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY: 502 means app startup failure")
    print("   Railway logs will show exactly what's wrong")
    print("   Install Railway CLI to see the actual error!")
    print("=" * 60)

if __name__ == "__main__":
    main()
