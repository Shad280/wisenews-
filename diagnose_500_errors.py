#!/usr/bin/env python3
"""
Diagnostic script to identify 500 errors in WiseNews routes
"""

def test_subscription_routes():
    """Test subscription-related functionality"""
    print("🔍 TESTING SUBSCRIPTION ROUTES")
    print("=" * 50)
    
    try:
        # Test subscription manager import
        from subscription_manager import SubscriptionManager
        print("✅ SubscriptionManager import - OK")
        
        # Test subscription manager initialization
        sub_manager = SubscriptionManager()
        print("✅ SubscriptionManager initialization - OK")
        
        # Test get_all_plans method
        plans = sub_manager.get_all_plans()
        print(f"✅ get_all_plans() - OK (found {len(plans)} plans)")
        
        # Test database connection
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check if subscription_plans table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscription_plans'")
        if cursor.fetchone():
            print("✅ subscription_plans table - EXISTS")
        else:
            print("❌ subscription_plans table - MISSING")
            
        # Check if user_subscriptions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_subscriptions'")
        if cursor.fetchone():
            print("✅ user_subscriptions table - EXISTS")
        else:
            print("❌ user_subscriptions table - MISSING")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Subscription test failed: {e}")
        import traceback
        traceback.print_exc()

def test_chat_routes():
    """Test chat-related functionality"""
    print("\n🔍 TESTING CHAT ROUTES")
    print("=" * 50)
    
    try:
        # Test support routes import
        from support_routes import support_bp
        print("✅ support_routes import - OK")
        
        # Test chatbot support import
        from chatbot_support import support_chatbot
        print("✅ chatbot_support import - OK")
        
        # Test chatbot initialization
        print(f"✅ support_chatbot object - OK (type: {type(support_chatbot)})")
        
        # Test database tables for chat
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check if chat_sessions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
        if cursor.fetchone():
            print("✅ chat_sessions table - EXISTS")
        else:
            print("❌ chat_sessions table - MISSING")
            
        # Check if chat_messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        if cursor.fetchone():
            print("✅ chat_messages table - EXISTS")
        else:
            print("❌ chat_messages table - MISSING")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        import traceback
        traceback.print_exc()

def test_report_routes():
    """Test report issue functionality"""
    print("\n🔍 TESTING REPORT ROUTES")
    print("=" * 50)
    
    try:
        # Search for report functionality in the codebase
        import os
        import re
        
        # Check if there are any report-related routes in app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
            
        # Look for report-related patterns
        report_patterns = [
            r'@app\.route.*report',
            r'def.*report.*issue',
            r'report.*bug',
            r'submit.*issue'
        ]
        
        found_reports = False
        for pattern in report_patterns:
            matches = re.findall(pattern, app_content, re.IGNORECASE)
            if matches:
                print(f"✅ Found report pattern: {matches}")
                found_reports = True
                
        if not found_reports:
            print("❌ No report routes found in app.py")
            
        # Check support_routes.py for report functionality
        try:
            with open('support_routes.py', 'r', encoding='utf-8') as f:
                support_content = f.read()
                
            for pattern in report_patterns:
                matches = re.findall(pattern, support_content, re.IGNORECASE)
                if matches:
                    print(f"✅ Found report pattern in support_routes: {matches}")
                    found_reports = True
                    
        except FileNotFoundError:
            print("❌ support_routes.py not found")
            
        if not found_reports:
            print("⚠️ No report issue functionality found - this might be the cause of the error")
            
    except Exception as e:
        print(f"❌ Report test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_files():
    """Test if required template files exist"""
    print("\n🔍 TESTING TEMPLATE FILES")
    print("=" * 50)
    
    import os
    
    required_templates = [
        'templates/subscription_plans.html',
        'templates/my_subscription.html', 
        'templates/chat_interface.html',
        'templates/support_center.html'
    ]
    
    for template in required_templates:
        if os.path.exists(template):
            print(f"✅ {template} - EXISTS")
        else:
            print(f"❌ {template} - MISSING")

def main():
    """Run all diagnostic tests"""
    print("🔄 DIAGNOSING 500 ERROR SOURCES")
    print("=" * 70)
    
    test_subscription_routes()
    test_chat_routes()
    test_report_routes()
    test_template_files()
    
    print("\n🎯 DIAGNOSTIC COMPLETE!")
    print("=" * 50)
    print("✅ Check the results above to identify the root cause of 500 errors")
    print("⚠️ Missing tables, files, or import errors will cause 500 errors")

if __name__ == "__main__":
    main()
