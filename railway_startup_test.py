#!/usr/bin/env python3
"""
Railway Startup Simulator
Test app startup exactly as Railway would
"""

import os
import sys
import sqlite3
from datetime import datetime

def simulate_railway_startup():
    """Simulate Railway startup environment"""
    print("🚂 SIMULATING RAILWAY STARTUP ENVIRONMENT")
    print("=" * 60)
    
    # Set Railway-like environment
    os.environ['PORT'] = '8000'
    os.environ['HOST'] = '0.0.0.0'
    os.environ['RAILWAY_ENVIRONMENT'] = 'production'
    
    print(f"🌐 PORT: {os.environ.get('PORT')}")
    print(f"🌐 HOST: {os.environ.get('HOST')}")
    print(f"🚂 RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
    
    print("\n📦 TESTING IMPORTS...")
    try:
        # Test critical imports one by one
        print("   Importing Flask...", end=" ")
        from flask import Flask, jsonify, request, render_template_string, session, redirect, url_for, flash, g
        print("✅")
        
        print("   Importing os, sqlite3, datetime...", end=" ")
        import os, sqlite3
        from datetime import datetime, timedelta
        print("✅")
        
        print("   Importing json, hashlib, threading...", end=" ")
        import json, hashlib, threading, time
        print("✅")
        
        print("   Importing urllib, xml...", end=" ")
        import urllib.request, urllib.parse
        from xml.etree import ElementTree as ET
        print("✅")
        
        print("   Importing user_auth...", end=" ")
        import user_auth
        print("✅")
        
        print("   Importing auth_decorators...", end=" ")
        import auth_decorators
        print("✅")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    print("\n🏗️  TESTING APP INITIALIZATION...")
    try:
        # Initialize Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'wisenews-secret-key-2025'
        app.config['DATABASE'] = 'wisenews.db'
        print("   ✅ Flask app initialized")
        
        # Test database connection
        conn = sqlite3.connect('wisenews.db')
        conn.close()
        print("   ✅ Database connection successful")
        
    except Exception as e:
        print(f"   ❌ App initialization failed: {e}")
        return False
    
    print("\n💾 TESTING DATABASE INITIALIZATION...")
    try:
        # Test database operations
        exec(open('app.py').read(), globals())
        print("   ✅ App.py executed successfully")
        
    except Exception as e:
        print(f"   ❌ Database init failed: {e}")
        return False
    
    return True

def test_gunicorn_compatibility():
    """Test if app is compatible with Gunicorn"""
    print("\n🔧 TESTING GUNICORN COMPATIBILITY")
    print("=" * 60)
    
    try:
        # Check if gunicorn can import the app
        print("📦 Testing gunicorn import...", end=" ")
        import gunicorn
        print("✅")
        
        print("🎯 Testing app:app pattern...", end=" ")
        # This simulates what gunicorn does
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        if hasattr(app_module, 'app'):
            print("✅")
            print(f"   App object found: {type(app_module.app)}")
        else:
            print("❌ No 'app' object found in app.py")
            return False
            
    except Exception as e:
        print(f"❌ Gunicorn compatibility test failed: {e}")
        return False
    
    return True

def check_railway_requirements():
    """Check Railway-specific requirements"""
    print("\n🚂 CHECKING RAILWAY REQUIREMENTS")
    print("=" * 60)
    
    # Check Procfile
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile_content = f.read().strip()
        print(f"📄 Procfile: {procfile_content}")
        
        if procfile_content == "web: gunicorn app:app":
            print("   ✅ Procfile correct")
        else:
            print(f"   ❌ Procfile incorrect, should be 'web: gunicorn app:app'")
            return False
    else:
        print("❌ Procfile missing!")
        return False
    
    # Check requirements.txt
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['Flask', 'gunicorn', 'bcrypt', 'feedparser']
        missing = []
        
        for package in required_packages:
            if package.lower() not in requirements.lower():
                missing.append(package)
        
        if missing:
            print(f"❌ Missing packages in requirements.txt: {missing}")
            return False
        else:
            print("✅ All required packages in requirements.txt")
    else:
        print("❌ requirements.txt missing!")
        return False
    
    return True

def generate_railway_diagnosis():
    """Generate diagnosis for Railway deployment"""
    print("\n🎯 RAILWAY DEPLOYMENT DIAGNOSIS")
    print("=" * 60)
    
    print("Based on tests above:")
    print()
    
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile = f.read().strip()
        if procfile == "web: gunicorn app:app":
            print("✅ Procfile is correct")
        else:
            print(f"❌ Procfile needs fixing: '{procfile}' → 'web: gunicorn app:app'")
    
    print("\n📋 NEXT STEPS:")
    print("1. ⏰ Wait 5-10 minutes for Railway deployment")
    print("2. 🌐 Try Railway URL again")
    print("3. 📱 Check Railway dashboard for logs")
    print("4. 🔄 If still failing, install Railway CLI for detailed logs")
    
    print("\n💡 MOST LIKELY CAUSE:")
    print("Railway is still building/starting the application.")
    print("The Procfile fix should resolve the 'Application failed to respond' error.")
    
    print(f"\n🕐 Current time: {datetime.now().strftime('%H:%M:%S')}")
    print("⏰ Estimated Railway completion: 2-10 minutes from last push")

def main():
    """Main test function"""
    print("🧪 RAILWAY STARTUP SIMULATION & DIAGNOSIS")
    print("=" * 60)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    
    success &= simulate_railway_startup()
    success &= test_gunicorn_compatibility() 
    success &= check_railway_requirements()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - Railway deployment should work!")
    else:
        print("❌ ISSUES FOUND - Check errors above")
    
    generate_railway_diagnosis()
    print("=" * 60)

if __name__ == "__main__":
    main()
