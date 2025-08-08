#!/usr/bin/env python3
"""
Focused test to reproduce 500 errors by simulating user interactions
"""

import sqlite3
import sys
from datetime import datetime

def test_subscription_route_without_login():
    """Test what happens when accessing subscription route without login"""
    print("🔍 Testing subscription route access without login...")
    try:
        # Simulate app context
        from flask import Flask
        from auth_decorators import login_required
        from subscription_manager import SubscriptionManager
        
        app = Flask(__name__)
        app.secret_key = 'test'
        
        with app.test_client() as client:
            # Try to access subscription plans without login
            response = client.get('/subscription-plans')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 500:
                print("❌ 500 ERROR on subscription route without login")
                return False
            else:
                print("✅ Subscription route handles no-login correctly")
                return True
                
    except Exception as e:
        print(f"❌ Error testing subscription route: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_route_access():
    """Test chat route access"""
    print("\n🔍 Testing chat route access...")
    try:
        from flask import Flask
        from support_routes import support_bp
        
        app = Flask(__name__)
        app.secret_key = 'test'
        app.register_blueprint(support_bp)
        
        with app.test_client() as client:
            # Test guest chat
            response = client.get('/support/chat/guest')
            print(f"   Guest chat status: {response.status_code}")
            
            if response.status_code == 500:
                print("❌ 500 ERROR on guest chat route")
                return False
            
            # Test support center
            response = client.get('/support')
            print(f"   Support center status: {response.status_code}")
            
            if response.status_code == 500:
                print("❌ 500 ERROR on support center route")
                return False
            
            print("✅ Chat routes accessible")
            return True
            
    except Exception as e:
        print(f"❌ Error testing chat routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_creation():
    """Test chat session creation directly"""
    print("\n🔍 Testing chat session creation...")
    try:
        from chatbot_support import support_chatbot
        
        # Test session creation
        session_id = support_chatbot.create_chat_session()
        print(f"   Session created: {session_id}")
        
        if not session_id:
            print("❌ Failed to create chat session")
            return False
        
        # Test message processing
        response = support_chatbot.process_message(session_id, "test message")
        print(f"   Message processed: {bool(response)}")
        
        if not response:
            print("❌ Failed to process message")
            return False
        
        print("✅ Chat session functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Error testing session creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_rendering():
    """Test if templates can be rendered"""
    print("\n🔍 Testing template rendering...")
    try:
        from flask import Flask, render_template
        import os
        
        app = Flask(__name__)
        
        # Check if templates exist
        templates = [
            'subscription_plans.html',
            'chat_interface.html', 
            'support_center.html'
        ]
        
        missing_templates = []
        for template in templates:
            template_path = os.path.join('templates', template)
            if not os.path.exists(template_path):
                missing_templates.append(template)
        
        if missing_templates:
            print(f"❌ Missing templates: {missing_templates}")
            return False
        
        print("✅ All templates exist")
        
        # Test basic template rendering with app context
        with app.app_context():
            try:
                # This should not fail even with no data
                html = render_template('support_center.html')
                print("✅ Template rendering works")
                return True
            except Exception as e:
                print(f"❌ Template rendering failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing templates: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_constraints():
    """Check for database constraint issues"""
    print("\n🔍 Checking database constraints...")
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check for foreign key issues
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        
        if fk_errors:
            print(f"❌ Foreign key constraint violations: {fk_errors}")
            return False
        
        # Check subscription plans data
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plans_count = cursor.fetchone()[0]
        
        if plans_count == 0:
            print("❌ No subscription plans in database")
            return False
        
        print(f"✅ Database has {plans_count} subscription plans")
        
        # Check chat tables
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions_count = cursor.fetchone()[0]
        print(f"✅ Database has {sessions_count} chat sessions")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database constraint check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run focused tests to identify 500 error sources"""
    print("🎯 FOCUSED 500 ERROR INVESTIGATION")
    print("=" * 50)
    
    tests = [
        ("Database Constraints", check_database_constraints),
        ("Template Rendering", test_template_rendering),
        ("Chat Session Creation", test_session_creation),
        ("Chat Route Access", test_chat_route_access),
        ("Subscription Route (No Login)", test_subscription_route_without_login),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 FOCUSED TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed != total:
        print("\n🚨 LIKELY 500 ERROR CAUSES:")
        for test_name, passed_test in results.items():
            if not passed_test:
                print(f"   - {test_name}")
        
        print("\n💡 RECOMMENDED FIXES:")
        if not results.get("Database Constraints", True):
            print("   1. Fix database foreign key constraints")
            print("   2. Ensure subscription plans are properly initialized")
        
        if not results.get("Template Rendering", True):
            print("   3. Check template syntax and required variables")
            print("   4. Ensure Flask app context is properly set")
        
        if not results.get("Chat Session Creation", True):
            print("   5. Fix chatbot initialization issues")
            print("   6. Check database table schema for chat system")
        
    else:
        print("\n🤔 All focused tests passed. 500 errors might be:")
        print("   1. Session/authentication context missing")
        print("   2. Missing required variables in template context")
        print("   3. Concurrent access or race conditions")
        print("   4. Environment-specific issues")

if __name__ == "__main__":
    main()
