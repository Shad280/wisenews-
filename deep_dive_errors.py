#!/usr/bin/env python3
"""
Deep dive test for session and authentication issues
"""

import sqlite3
import requests
import time
from datetime import datetime

def test_authentication_flow():
    """Test authentication flow that might be causing issues"""
    print("🔍 TESTING AUTHENTICATION FLOW")
    print("=" * 50)
    
    try:
        base_url = "http://127.0.0.1:5000"
        
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Test 1: Try to access protected routes without login
        protected_routes = [
            "/my-subscription",
            "/subscription-plans", 
            "/support/chat"
        ]
        
        print("Testing protected routes without authentication:")
        for route in protected_routes:
            try:
                response = session.get(f"{base_url}{route}", allow_redirects=False)
                print(f"   {route}: Status {response.status_code}")
                
                if response.status_code == 500:
                    print(f"      ❌ 500 ERROR: {response.text[:200]}...")
                elif response.status_code == 302:
                    print(f"      ✅ Redirect (expected for protected routes)")
                
            except Exception as e:
                print(f"   {route}: ❌ Error - {e}")
        
        # Test 2: Try login flow
        print("\nTesting login flow:")
        try:
            # Get login page
            login_response = session.get(f"{base_url}/login")
            print(f"   Login page: Status {login_response.status_code}")
            
            # Try login with test credentials
            login_data = {
                'username': 'testuser',
                'password': 'testpass'
            }
            
            login_submit = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
            print(f"   Login submit: Status {login_submit.status_code}")
            
        except Exception as e:
            print(f"   Login test: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication flow test failed: {e}")
        return False

def test_session_management():
    """Test session management issues"""
    print("\n🔍 TESTING SESSION MANAGEMENT")
    print("=" * 50)
    
    try:
        from user_auth import user_manager
        
        # Test session validation
        print("Testing session validation:")
        
        # Test with invalid session
        is_valid, user_data = user_manager.validate_session("invalid_token")
        print(f"   Invalid session: {is_valid} (should be False)")
        
        # Test user lookup
        try:
            user = user_manager.get_user_by_id(1)
            if user:
                print(f"   User lookup working: User {user.get('username', 'unknown')}")
            else:
                print("   ⚠️ User lookup returned None")
        except Exception as e:
            print(f"   ❌ User lookup error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_rendering_with_context():
    """Test template rendering with proper context"""
    print("\n🔍 TESTING TEMPLATE RENDERING WITH CONTEXT")
    print("=" * 50)
    
    try:
        from flask import Flask, render_template
        from subscription_manager import SubscriptionManager
        
        app = Flask(__name__)
        
        with app.app_context():
            # Test subscription template with data
            try:
                manager = SubscriptionManager()
                plans = manager.get_all_plans()
                
                # Try rendering with minimal context
                html = render_template('subscription_plans.html', 
                                     plans=plans, 
                                     current_subscription=None,
                                     daily_usage={'calls': 0, 'limit': 100})
                
                print("   ✅ Subscription template renders with context")
                
            except Exception as e:
                print(f"   ❌ Subscription template error: {e}")
                import traceback
                traceback.print_exc()
            
            # Test chat template
            try:
                html = render_template('chat_interface.html', user=None, session_id=123)
                print("   ✅ Chat template renders with context")
                
            except Exception as e:
                print(f"   ❌ Chat template error: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Template rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_missing_template_variables():
    """Check for missing template variables that could cause errors"""
    print("\n🔍 CHECKING FOR MISSING TEMPLATE VARIABLES")
    print("=" * 50)
    
    try:
        import re
        
        templates_to_check = [
            'templates/subscription_plans.html',
            'templates/chat_interface.html',
            'templates/my_subscription.html'
        ]
        
        for template_path in templates_to_check:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all template variables
                variables = re.findall(r'\{\{\s*([^}]+)\s*\}\}', content)
                
                print(f"   {template_path}:")
                
                # Check for common problematic patterns
                for var in variables:
                    var = var.strip()
                    if '.' in var and 'if' not in var and 'for' not in var:
                        # This could be a problem if the object is None
                        print(f"      ⚠️ Potential issue: {{{{ {var} }}}}")
                
                # Check for undefined variables (basic check)
                undefined_patterns = [
                    r'\{\{\s*[^}]*undefined[^}]*\}\}',
                    r'\{\{\s*[^}]*None\.[^}]*\}\}'
                ]
                
                for pattern in undefined_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"      ❌ Found undefined patterns: {matches}")
                
            except Exception as e:
                print(f"   ❌ Error checking {template_path}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template variable check failed: {e}")
        return False

def test_actual_user_flow():
    """Test the actual user flow that might be causing errors"""
    print("\n🔍 TESTING ACTUAL USER FLOW")
    print("=" * 50)
    
    try:
        # Simulate user accessing features
        from subscription_manager import SubscriptionManager
        from chatbot_support import support_chatbot
        
        manager = SubscriptionManager()
        
        # Test subscription flow for existing user
        print("Testing subscription flow:")
        user_id = 1  # Existing user
        
        try:
            subscription = manager.get_user_subscription(user_id)
            print(f"   ✅ User subscription: {subscription}")
            
            plans = manager.get_all_plans()
            print(f"   ✅ Available plans: {len(plans)}")
            
            usage = manager.get_daily_usage(user_id)
            print(f"   ✅ Daily usage: {usage}")
            
        except Exception as e:
            print(f"   ❌ Subscription flow error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test chat flow
        print("\nTesting chat flow:")
        try:
            session_id = support_chatbot.create_chat_session(user_id)
            print(f"   ✅ Chat session created: {session_id}")
            
            response = support_chatbot.process_message(session_id, "I need help with my account")
            print(f"   ✅ Message processed: {response.get('message', 'No message')[:50]}...")
            
        except Exception as e:
            print(f"   ❌ Chat flow error: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ User flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_flask_error_handling():
    """Check Flask error handling configuration"""
    print("\n🔍 CHECKING FLASK ERROR HANDLING")
    print("=" * 50)
    
    try:
        import app
        flask_app = app.app
        
        # Check if app is in debug mode
        print(f"   Debug mode: {flask_app.debug}")
        print(f"   Testing mode: {flask_app.testing}")
        
        # Check error handlers
        error_handlers = flask_app.error_handler_spec
        print(f"   Error handlers configured: {len(error_handlers) if error_handlers else 0}")
        
        # Check if there are any app context issues
        try:
            with flask_app.app_context():
                print("   ✅ App context works")
        except Exception as e:
            print(f"   ❌ App context error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask error handling check failed: {e}")
        return False

def main():
    """Run deep dive error investigation"""
    print("🔍 DEEP DIVE ERROR INVESTIGATION")
    print("=" * 60)
    
    tests = [
        ("Session Management", test_session_management),
        ("Template Rendering", test_template_rendering_with_context),
        ("Template Variables", check_missing_template_variables),
        ("User Flow", test_actual_user_flow),
        ("Flask Error Handling", check_flask_error_handling),
        ("Authentication Flow", test_authentication_flow),
    ]
    
    results = {}
    issues_found = []
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
            issues_found.append(f"{test_name}: {e}")
    
    print(f"\n📊 DEEP DIVE RESULTS:")
    passed = 0
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Deep Dive Score: {passed}/{len(results)}")
    
    if issues_found:
        print(f"\n🚨 SPECIFIC ISSUES FOUND:")
        for issue in issues_found:
            print(f"   - {issue}")
    
    if passed < len(results):
        print(f"\n💡 LIKELY CAUSES OF YOUR ERRORS:")
        print("   1. Session/authentication context missing")
        print("   2. Template variables not properly passed")
        print("   3. User not logged in when accessing protected routes")
        print("   4. Database connection issues during request processing")
        
        print(f"\n🔧 RECOMMENDED FIXES:")
        print("   1. Ensure user is logged in before accessing protected features")
        print("   2. Add proper error handling to template rendering")
        print("   3. Check browser console for JavaScript errors")
        print("   4. Clear browser cache and cookies")
    else:
        print(f"\n🤔 All backend tests pass. The errors might be:")
        print("   1. Browser-side JavaScript errors")
        print("   2. Network connectivity issues")
        print("   3. Cached content causing problems")
        print("   4. Race conditions during page load")

if __name__ == "__main__":
    main()
