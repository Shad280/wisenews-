#!/usr/bin/env python3
"""
Railway Deployment Diagnostic Tool
Checks for common deployment issues and provides fixes
"""

import os
import sys
import sqlite3
from pathlib import Path

def check_file_structure():
    """Check if all required files exist"""
    print("🔍 Checking File Structure...")
    required_files = [
        'app.py',
        'requirements.txt',
        'user_auth.py', 
        'auth_decorators.py',
        'Procfile'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")
    
    return missing_files

def check_requirements():
    """Check requirements.txt for essential packages"""
    print("\n📦 Checking Requirements...")
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        return False
    
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    essential_packages = [
        'Flask',
        'gunicorn',
        'bcrypt',
        'feedparser',
        'requests'
    ]
    
    missing_packages = []
    for package in essential_packages:
        if package.lower() not in requirements.lower():
            missing_packages.append(package)
            print(f"❌ Missing package: {package}")
        else:
            print(f"✅ Found package: {package}")
    
    return len(missing_packages) == 0

def check_procfile():
    """Check if Procfile exists and is correct"""
    print("\n🚀 Checking Procfile...")
    if not os.path.exists('Procfile'):
        print("❌ Procfile not found!")
        return False
    
    with open('Procfile', 'r') as f:
        content = f.read().strip()
    
    expected_content = "web: gunicorn app:app"
    if content == expected_content:
        print(f"✅ Procfile correct: {content}")
        return True
    else:
        print(f"❌ Procfile incorrect: {content}")
        print(f"   Should be: {expected_content}")
        return False

def check_app_py_syntax():
    """Check if app.py has syntax errors"""
    print("\n🐍 Checking app.py Syntax...")
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, 'app.py', 'exec')
        print("✅ app.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in app.py:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def check_database_setup():
    """Check database initialization"""
    print("\n💾 Checking Database Setup...")
    
    # Check if database exists
    if os.path.exists('wisenews.db'):
        print("✅ Database file exists")
        try:
            conn = sqlite3.connect('wisenews.db')
            cursor = conn.cursor()
            
            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'user_sessions', 'articles', 'categories']
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table exists: {table}")
                else:
                    missing_tables.append(table)
                    print(f"❌ Missing table: {table}")
            
            conn.close()
            return len(missing_tables) == 0
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    else:
        print("⚠️  Database file doesn't exist (will be created on startup)")
        return True

def check_imports():
    """Check if all imports in app.py are available"""
    print("\n📚 Checking Python Imports...")
    
    try:
        # Test critical imports
        import flask
        print("✅ Flask imported successfully")
        
        import bcrypt
        print("✅ bcrypt imported successfully")
        
        import feedparser
        print("✅ feedparser imported successfully")
        
        import sqlite3
        print("✅ sqlite3 imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def generate_fixes():
    """Generate fix commands for common issues"""
    print("\n🔧 POTENTIAL FIXES:")
    print("=" * 50)
    
    print("\n1. 📦 Install Railway CLI:")
    print("   npm install -g @railway/cli")
    print("   railway login")
    print("   railway logs")
    
    print("\n2. 🚀 Check Railway Status:")
    print("   Visit: https://railway.app/dashboard")
    print("   Check your project's deployment logs")
    
    print("\n3. 🔄 Force Redeploy:")
    print("   git add .")
    print("   git commit -m \"Force redeploy to fix Railway issues\"")
    print("   git push origin main")
    
    print("\n4. 🐛 Check for Common Issues:")
    print("   - Port binding (Railway uses PORT env variable)")
    print("   - File permissions")
    print("   - Memory limits")
    print("   - Database initialization errors")
    
    print("\n5. 🆘 Emergency Local Test:")
    print("   python app.py")
    print("   (Test locally first)")

def main():
    """Main diagnostic function"""
    print("🚂 RAILWAY DEPLOYMENT DIAGNOSTIC")
    print("=" * 50)
    
    # Run all checks
    issues = []
    
    missing_files = check_file_structure()
    if missing_files:
        issues.append(f"Missing files: {', '.join(missing_files)}")
    
    if not check_requirements():
        issues.append("Missing required packages")
    
    if not check_procfile():
        issues.append("Procfile issues")
    
    if not check_app_py_syntax():
        issues.append("app.py syntax errors")
    
    if not check_database_setup():
        issues.append("Database setup problems")
    
    if not check_imports():
        issues.append("Python import errors")
    
    print("\n" + "=" * 50)
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("✅ ALL CHECKS PASSED!")
        print("   Issue might be Railway-specific (memory, ports, etc.)")
    
    generate_fixes()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Fix any issues found above")
    print("2. Install Railway CLI to check logs")
    print("3. Test locally with 'python app.py'")
    print("4. Force redeploy to Railway")

if __name__ == "__main__":
    main()
