#!/usr/bin/env python3
"""
Test script to identify the exact causes of 500 errors
"""

import sqlite3
import sys
import traceback
from datetime import datetime

def test_database_connectivity():
    """Test basic database connection"""
    print("🔍 Testing database connectivity...")
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database connected. Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_subscription_imports():
    """Test subscription manager imports"""
    print("\n🔍 Testing subscription manager imports...")
    try:
        from subscription_manager import SubscriptionManager
        manager = SubscriptionManager()
        print("✅ SubscriptionManager imported successfully")
        
        # Test method calls
        plans = manager.get_all_plans()
        print(f"✅ get_all_plans() returned {len(plans)} plans")
        return True
    except Exception as e:
        print(f"❌ Subscription manager import failed: {e}")
        traceback.print_exc()
        return False

def test_chatbot_imports():
    """Test chatbot imports"""
    print("\n🔍 Testing chatbot imports...")
    try:
        from chatbot_support import support_chatbot
        print("✅ Chatbot imported successfully")
        
        # Test session creation
        session_id = support_chatbot.create_chat_session()
        print(f"✅ Chat session created: {session_id}")
        return True
    except Exception as e:
        print(f"❌ Chatbot import failed: {e}")
        traceback.print_exc()
        return False

def test_auth_decorators():
    """Test auth decorators"""
    print("\n🔍 Testing auth decorators...")
    try:
        from auth_decorators import login_required, get_current_user
        print("✅ Auth decorators imported successfully")
        return True
    except Exception as e:
        print(f"❌ Auth decorators import failed: {e}")
        traceback.print_exc()
        return False

def test_support_routes():
    """Test support routes imports"""
    print("\n🔍 Testing support routes...")
    try:
        from support_routes import support_bp
        print("✅ Support routes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Support routes import failed: {e}")
        traceback.print_exc()
        return False

def check_required_tables():
    """Check for required database tables"""
    print("\n🔍 Checking required database tables...")
    required_tables = [
        'subscription_plans',
        'user_subscriptions', 
        'chat_sessions',
        'chat_messages',
        'support_tickets',
        'knowledge_base',
        'users'
    ]
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        missing_tables = []
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables exist")
            return True
            
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_template_existence():
    """Check if required templates exist"""
    print("\n🔍 Checking template files...")
    import os
    
    required_templates = [
        'templates/subscription_plans.html',
        'templates/chat_interface.html',
        'templates/support_center.html'
    ]
    
    missing_templates = []
    for template in required_templates:
        if not os.path.exists(template):
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ Missing templates: {missing_templates}")
        return False
    else:
        print("✅ All required templates exist")
        return True

def simulate_subscription_flow():
    """Test subscription functionality"""
    print("\n🔍 Testing subscription flow...")
    try:
        from subscription_manager import SubscriptionManager
        manager = SubscriptionManager()
        
        # Test getting plans
        plans = manager.get_all_plans()
        if not plans:
            print("❌ No subscription plans found")
            return False
        
        print(f"✅ Found {len(plans)} subscription plans:")
        for plan in plans:
            print(f"   - {plan.get('name', 'Unknown')}: ${plan.get('price', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Subscription flow test failed: {e}")
        traceback.print_exc()
        return False

def simulate_chat_flow():
    """Test chat functionality"""
    print("\n🔍 Testing chat flow...")
    try:
        from chatbot_support import support_chatbot
        
        # Create session
        session_id = support_chatbot.create_chat_session()
        if not session_id:
            print("❌ Failed to create chat session")
            return False
        
        # Send test message
        response = support_chatbot.process_message(session_id, "Hello, I need help")
        if not response or 'message' not in response:
            print("❌ Failed to process message")
            return False
        
        print("✅ Chat flow working:")
        print(f"   Session: {session_id}")
        print(f"   Response: {response['message'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Chat flow test failed: {e}")
        traceback.print_exc()
        return False

def check_flask_app_setup():
    """Check if Flask app can be imported"""
    print("\n🔍 Testing Flask app setup...")
    try:
        # Try importing the main app components
        from flask import Flask
        print("✅ Flask imported")
        
        # Check if we can import app components
        import app
        print("✅ Main app module imported")
        
        return True
    except Exception as e:
        print(f"❌ Flask app setup failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING 500 ERROR DIAGNOSIS")
    print("=" * 50)
    
    tests = [
        ("Database Connectivity", test_database_connectivity),
        ("Required Tables", check_required_tables),
        ("Template Files", test_template_existence),
        ("Auth Decorators", test_auth_decorators),
        ("Subscription Imports", test_subscription_imports),
        ("Chatbot Imports", test_chatbot_imports),
        ("Support Routes", test_support_routes),
        ("Flask App Setup", check_flask_app_setup),
        ("Subscription Flow", simulate_subscription_flow),
        ("Chat Flow", simulate_chat_flow)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed != total:
        print("\n🚨 IDENTIFIED ISSUES:")
        for test_name, passed_test in results.items():
            if not passed_test:
                print(f"   - {test_name}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Fix the failing components above")
        print("   2. Check error logs for detailed information")
        print("   3. Ensure all dependencies are installed")
        print("   4. Verify database schema is complete")
    else:
        print("\n🎉 All tests passed! The 500 errors might be:")
        print("   1. Runtime/request-specific issues")
        print("   2. Missing session/authentication context")
        print("   3. Template rendering problems")
        print("   4. Network or deployment issues")

if __name__ == "__main__":
    main()
