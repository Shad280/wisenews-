#!/usr/bin/env python3
"""
Deployment check script for WiseNews 3.0.0
This script helps verify that all components are working correctly
"""

import os
import sys

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking imports...")
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask: {e}")
        return False
    
    try:
        import feedparser
        print(f"✅ Feedparser: {feedparser.__version__}")
    except ImportError as e:
        print(f"❌ Feedparser: {e}")
        return False
    
    try:
        import bcrypt
        print(f"✅ Bcrypt: {bcrypt.__version__}")
    except ImportError as e:
        print(f"❌ Bcrypt: {e}")
        return False
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests: {e}")
        return False
    
    try:
        import schedule
        print(f"✅ Schedule: available")
    except ImportError as e:
        print(f"❌ Schedule: {e}")
        return False
    
    return True

def check_files():
    """Check if all required files exist"""
    print("\n📁 Checking files...")
    
    required_files = [
        'app.py',
        'user_auth.py', 
        'auth_decorators.py',
        'requirements.txt',
        'Procfile',
        'start.sh'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
            all_exist = False
    
    return all_exist

def check_database():
    """Check if database can be initialized"""
    print("\n🗄️ Checking database...")
    
    try:
        # Import the database functions
        sys.path.append('.')
        from app import init_db, get_db
        
        # Initialize database
        init_db()
        print("✅ Database initialization successful")
        
        # Test database connection
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM articles')
        count = cursor.fetchone()[0]
        print(f"✅ Database connection successful - {count} articles")
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main deployment check"""
    print("🚀 WiseNews 3.0.0 Deployment Check")
    print("=" * 40)
    
    # Check imports
    imports_ok = check_imports()
    
    # Check files
    files_ok = check_files()
    
    # Check database
    db_ok = check_database()
    
    print("\n" + "=" * 40)
    if imports_ok and files_ok and db_ok:
        print("✅ All checks passed! Deployment should work correctly.")
        print("🌐 WiseNews 3.0.0 is ready for production!")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
