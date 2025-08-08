#!/usr/bin/env python3
"""
Test specific routes that are showing errors
"""

import requests
import time
import subprocess
import sys
from multiprocessing import Process
import os

def start_flask_server():
    """Start Flask server for testing"""
    try:
        os.chdir(r"c:\Users\Stamo\news scrapper")
        subprocess.run([sys.executable, "app.py"], check=True)
    except Exception as e:
        print(f"Failed to start Flask server: {e}")

def test_problematic_routes():
    """Test the routes that are showing errors"""
    print("🔍 TESTING PROBLEMATIC ROUTES")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # Routes to test
    routes_to_test = [
        ("/support/chat", "Start Chat"),
        ("/support", "Support Center / Report Issue"),
        ("/my-subscription", "My Subscription"),
        ("/subscription-plans", "Subscription Plans"),
        ("/support/chat/guest", "Guest Chat"),
        ("/api/chat/send", "Chat API (POST)"),
    ]
    
    results = {}
    
    for route, description in routes_to_test:
        try:
            print(f"\n🔍 Testing {description}: {route}")
            
            if route == "/api/chat/send":
                # Test POST request
                response = requests.post(
                    f"{base_url}{route}",
                    json={"message": "test"},
                    timeout=10,
                    allow_redirects=False
                )
            else:
                # Test GET request
                response = requests.get(
                    f"{base_url}{route}",
                    timeout=10,
                    allow_redirects=False
                )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 500:
                print(f"   ❌ 500 ERROR DETECTED!")
                print(f"   Response: {response.text[:300]}...")
                results[description] = False
            elif response.status_code in [200, 302, 401, 403]:
                print(f"   ✅ Working (Status: {response.status_code})")
                results[description] = True
            else:
                print(f"   ⚠️ Unexpected status: {response.status_code}")
                results[description] = False
                
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Cannot connect to server")
            results[description] = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[description] = False
    
    return results

def check_route_imports():
    """Check if route imports are working correctly"""
    print("\n🔍 CHECKING ROUTE IMPORTS")
    print("=" * 50)
    
    try:
        # Test support routes
        from support_routes import support_bp
        print("✅ Support routes imported")
        
        # Test app routes
        import app
        print("✅ Main app imported")
        
        # Test if blueprints are registered
        flask_app = app.app
        blueprints = flask_app.blueprints
        print(f"✅ Registered blueprints: {list(blueprints.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_template_issues():
    """Check for template-related issues"""
    print("\n🔍 CHECKING TEMPLATE ISSUES")
    print("=" * 50)
    
    try:
        import os
        
        templates_to_check = [
            'templates/chat_interface.html',
            'templates/support_center.html', 
            'templates/subscription_plans.html',
            'templates/my_subscription.html'
        ]
        
        for template in templates_to_check:
            if os.path.exists(template):
                with open(template, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 100:
                        print(f"⚠️ {template} seems too small")
                    else:
                        print(f"✅ {template} exists and readable")
            else:
                print(f"❌ Missing template: {template}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template check error: {e}")
        return False

def check_database_connections():
    """Check for database connection issues"""
    print("\n🔍 CHECKING DATABASE CONNECTIONS")
    print("=" * 50)
    
    try:
        import sqlite3
        
        # Test basic connection
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Test chat tables
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions = cursor.fetchone()[0]
        print(f"✅ Chat sessions table: {sessions} records")
        
        # Test subscription tables
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plans = cursor.fetchone()[0]
        print(f"✅ Subscription plans: {plans} records")
        
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions")
        user_subs = cursor.fetchone()[0]
        print(f"✅ User subscriptions: {user_subs} records")
        
        # Test users table
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        print(f"✅ Users table: {users} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive route testing"""
    print("🚀 INVESTIGATING NEW ROUTE ERRORS")
    print("=" * 60)
    
    # Run checks
    import_ok = check_route_imports()
    template_ok = check_template_issues()
    db_ok = check_database_connections()
    
    print(f"\n📊 PRELIMINARY CHECKS:")
    print(f"   Imports: {'✅' if import_ok else '❌'}")
    print(f"   Templates: {'✅' if template_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    
    if not all([import_ok, template_ok, db_ok]):
        print("\n⚠️ Found issues in preliminary checks. Fixing these first...")
        return False
    
    print("\n🔄 Starting Flask server to test routes...")
    
    # Start server in background
    server_process = Process(target=start_flask_server)
    server_process.start()
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test routes
        route_results = test_problematic_routes()
        
        print(f"\n📊 ROUTE TEST RESULTS:")
        failed_routes = []
        for route, success in route_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {route}")
            if not success:
                failed_routes.append(route)
        
        if failed_routes:
            print(f"\n🚨 FAILED ROUTES: {failed_routes}")
            print("These routes need immediate attention!")
        else:
            print(f"\n🎉 All routes working correctly!")
            
    finally:
        # Clean up server
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
    
    return len(failed_routes) == 0 if 'failed_routes' in locals() else False

if __name__ == "__main__":
    main()
