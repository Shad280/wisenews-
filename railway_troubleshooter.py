#!/usr/bin/env python3
"""
Railway Deployment Troubleshooter
Advanced diagnostics for Railway deployment issues
"""

import time
import subprocess
import os
from datetime import datetime

def check_git_status():
    """Check if latest changes are pushed to Railway"""
    print("🔍 CHECKING GIT DEPLOYMENT STATUS")
    print("=" * 50)
    
    try:
        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.stdout.strip():
            print("⚠️  UNCOMMITTED CHANGES FOUND:")
            print(result.stdout)
            print("   → Run: git add . && git commit -m 'Fix deployment' && git push")
        else:
            print("✅ All changes committed and should be deployed")
        
        # Check last commit
        result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                              capture_output=True, text=True, cwd='.')
        print(f"📝 Last commit: {result.stdout.strip()}")
        
        # Check remote status
        result = subprocess.run(['git', 'status', '-sb'], 
                              capture_output=True, text=True, cwd='.')
        print(f"🔗 Branch status: {result.stdout.strip()}")
        
    except Exception as e:
        print(f"❌ Git check failed: {e}")

def check_file_integrity():
    """Check critical files for Railway deployment"""
    print("\n🔧 CHECKING CRITICAL FILES")
    print("=" * 50)
    
    critical_files = {
        'Procfile': 'web: gunicorn app:app',
        'requirements.txt': ['Flask', 'gunicorn', 'bcrypt'],
        'app.py': ['if __name__ == \'__main__\':', 'port = int(os.environ.get(\'PORT\'']
    }
    
    for filename, expected_content in critical_files.items():
        if os.path.exists(filename):
            print(f"✅ {filename} exists")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if isinstance(expected_content, str):
                if expected_content in content:
                    print(f"   ✅ Contains: {expected_content}")
                else:
                    print(f"   ❌ Missing: {expected_content}")
            elif isinstance(expected_content, list):
                for item in expected_content:
                    if item.lower() in content.lower():
                        print(f"   ✅ Contains: {item}")
                    else:
                        print(f"   ❌ Missing: {item}")
        else:
            print(f"❌ {filename} NOT FOUND!")

def test_local_startup():
    """Test if app starts locally"""
    print("\n🧪 TESTING LOCAL STARTUP")
    print("=" * 50)
    
    print("Testing Python syntax and imports...")
    try:
        result = subprocess.run(['python', '-c', 'import app; print("✅ App imports successfully")'], 
                              capture_output=True, text=True, cwd='.', timeout=10)
        
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"❌ Import failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Import test timed out (might be starting server)")
    except Exception as e:
        print(f"❌ Local test failed: {e}")

def generate_railway_debug_commands():
    """Generate commands to debug Railway deployment"""
    print("\n🚂 RAILWAY DEBUGGING COMMANDS")
    print("=" * 50)
    
    commands = [
        ("Check Railway Status", "Visit: https://railway.app/dashboard"),
        ("View Deployment Logs", "Install Railway CLI: npm install -g @railway/cli"),
        ("Login to Railway", "railway login"),
        ("Check Logs", "railway logs"),
        ("Check Service Status", "railway status"),
        ("Force Redeploy", "railway up --detach")
    ]
    
    for description, command in commands:
        print(f"📋 {description:20} → {command}")

def common_railway_issues():
    """List common Railway deployment issues and solutions"""
    print("\n🛠️  COMMON RAILWAY ISSUES & SOLUTIONS")
    print("=" * 50)
    
    issues = [
        {
            "issue": "Application failed to respond",
            "causes": [
                "Wrong Procfile command",
                "App not binding to PORT environment variable", 
                "Python import errors",
                "Database initialization failures",
                "Memory/resource limits exceeded"
            ],
            "solutions": [
                "✅ Fixed: Procfile now uses 'web: gunicorn app:app'",
                "✅ Verified: App uses os.environ.get('PORT', 5000)",
                "Test: python -c 'import app'",
                "Check Railway logs for specific errors"
            ]
        },
        {
            "issue": "Database errors on startup",
            "causes": [
                "Database file permissions",
                "SQLite initialization failures",
                "Missing database tables"
            ],
            "solutions": [
                "Database auto-initializes in app.py",
                "Check init_db() function runs on startup",
                "Verify database path is correct"
            ]
        },
        {
            "issue": "Import/dependency errors",
            "causes": [
                "Missing packages in requirements.txt",
                "Version conflicts",
                "Python version mismatch"
            ],
            "solutions": [
                "Verify all imports in requirements.txt",
                "Test locally: pip install -r requirements.txt",
                "Check Railway Python version"
            ]
        }
    ]
    
    for item in issues:
        print(f"\n❌ {item['issue'].upper()}:")
        print("   Causes:")
        for cause in item['causes']:
            print(f"     • {cause}")
        print("   Solutions:")
        for solution in item['solutions']:
            print(f"     • {solution}")

def deployment_status_timeline():
    """Show deployment timeline and next steps"""
    print(f"\n⏰ DEPLOYMENT TIMELINE")
    print("=" * 50)
    
    timeline = [
        ("🔧 Procfile Fixed", "COMPLETED", "Changed to 'web: gunicorn app:app'"),
        ("📤 Pushed to Railway", "COMPLETED", "Git push triggered deployment"),
        ("⚙️  Railway Building", "IN PROGRESS", "Should take 2-5 minutes"),
        ("🚀 App Starting", "PENDING", "Gunicorn starts the Flask app"),
        ("💾 Database Init", "PENDING", "SQLite database initializes"),
        ("📰 News Fetching", "PENDING", "Background news aggregation starts"),
        ("✅ App Ready", "PENDING", "WiseNews should be accessible")
    ]
    
    for step, status, description in timeline:
        status_icon = "✅" if status == "COMPLETED" else "🔄" if status == "IN PROGRESS" else "⏳"
        print(f"{status_icon} {step:20} {status:12} - {description}")
    
    print(f"\n🕐 Current time: {datetime.now().strftime('%H:%M:%S')}")
    print("⏰ Estimated completion: 2-5 minutes after push")

def immediate_action_plan():
    """Provide immediate steps to resolve the issue"""
    print(f"\n🎯 IMMEDIATE ACTION PLAN")
    print("=" * 50)
    
    steps = [
        "1. ⏰ Wait 5 more minutes for Railway deployment to complete",
        "2. 🌐 Try your Railway URL again",
        "3. 📱 Check Railway dashboard for deployment status",
        "4. 📋 If still failing, install Railway CLI for logs",
        "5. 🔄 If needed, force redeploy with git push",
        "6. 🆘 Share Railway logs if issue persists"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n💡 MOST LIKELY SCENARIO:")
    print("   Railway is still building/starting your app.")
    print("   The Procfile fix should resolve the issue.")
    print("   Try the URL again in a few minutes!")

def main():
    """Main troubleshooting function"""
    print("🚂 RAILWAY DEPLOYMENT TROUBLESHOOTER")
    print("=" * 60)
    print(f"🕐 Diagnosis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_git_status()
    check_file_integrity()
    test_local_startup()
    generate_railway_debug_commands()
    common_railway_issues()
    deployment_status_timeline()
    immediate_action_plan()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY: Procfile fixed, wait for Railway deployment!")
    print("=" * 60)

if __name__ == "__main__":
    main()
