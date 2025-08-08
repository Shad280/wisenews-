#!/usr/bin/env python3
"""
Comprehensive system check to identify ALL remaining errors
"""

import sqlite3
import os
import sys
import traceback
from datetime import datetime
import json

def test_database_integrity():
    """Check database for any integrity issues"""
    print("🔍 TESTING DATABASE INTEGRITY")
    print("=" * 50)
    
    issues = []
    
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        
        if fk_violations:
            issues.append(f"Foreign key violations: {fk_violations}")
            print(f"❌ Foreign key violations found: {len(fk_violations)}")
        else:
            print("✅ Foreign key constraints OK")
        
        # Check table integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result != "ok":
            issues.append(f"Database integrity issue: {integrity_result}")
            print(f"❌ Database integrity issue: {integrity_result}")
        else:
            print("✅ Database integrity OK")
        
        # Check for empty critical tables
        critical_tables = ['subscription_plans', 'users', 'articles']
        for table in critical_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0 and table in ['subscription_plans']:
                    issues.append(f"Critical table {table} is empty")
                    print(f"❌ Critical table {table} is empty")
                else:
                    print(f"✅ Table {table}: {count} records")
            except Exception as e:
                issues.append(f"Error checking table {table}: {e}")
                print(f"❌ Error checking table {table}: {e}")
        
        conn.close()
        return len(issues) == 0, issues
        
    except Exception as e:
        error = f"Database integrity check failed: {e}"
        print(f"❌ {error}")
        return False, [error]

def test_core_imports():
    """Test all core module imports"""
    print("\n🔍 TESTING CORE IMPORTS")
    print("=" * 50)
    
    import_tests = [
        ('app', 'Main application'),
        ('subscription_manager', 'Subscription manager'),
        ('chatbot_support', 'Chatbot support'),
        ('support_routes', 'Support routes'),
        ('auth_decorators', 'Authentication decorators'),
        ('user_auth', 'User authentication'),
        ('news_aggregator', 'News aggregator'),
        ('live_events_manager', 'Live events manager'),
        ('social_media_manager', 'Social media manager'),
        ('notification_manager', 'Notification manager'),
    ]
    
    failed_imports = []
    
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"✅ {description}")
        except Exception as e:
            error = f"{description}: {e}"
            failed_imports.append(error)
            print(f"❌ {description}: {e}")
    
    return len(failed_imports) == 0, failed_imports

def test_subscription_system():
    """Test subscription system thoroughly"""
    print("\n🔍 TESTING SUBSCRIPTION SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        from subscription_manager import SubscriptionManager
        manager = SubscriptionManager()
        
        # Test getting plans
        plans = manager.get_all_plans()
        if not plans:
            issues.append("No subscription plans available")
            print("❌ No subscription plans available")
        else:
            print(f"✅ {len(plans)} subscription plans available")
            
            # Test plan structure
            required_fields = ['id', 'name', 'price_monthly', 'max_articles_per_day']
            for plan in plans:
                missing_fields = [field for field in required_fields if field not in plan]
                if missing_fields:
                    issues.append(f"Plan {plan.get('name', 'unknown')} missing fields: {missing_fields}")
                    print(f"❌ Plan {plan.get('name', 'unknown')} missing fields: {missing_fields}")
            
            if not issues:
                print("✅ All plans have required fields")
        
        # Test subscription checking for a user
        try:
            test_subscription = manager.get_user_subscription(1)  # Test user 1
            print(f"✅ User subscription check working")
        except Exception as e:
            issues.append(f"User subscription check failed: {e}")
            print(f"❌ User subscription check failed: {e}")
        
        # Test usage tracking
        try:
            usage = manager.get_daily_usage(1)  # Test user 1
            print(f"✅ Usage tracking working")
        except Exception as e:
            issues.append(f"Usage tracking failed: {e}")
            print(f"❌ Usage tracking failed: {e}")
        
    except Exception as e:
        error = f"Subscription system import/init failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_chat_system():
    """Test chat system thoroughly"""
    print("\n🔍 TESTING CHAT SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        from chatbot_support import support_chatbot
        
        # Test session creation
        session_id = support_chatbot.create_chat_session()
        if not session_id:
            issues.append("Chat session creation failed")
            print("❌ Chat session creation failed")
        else:
            print(f"✅ Chat session created: {session_id}")
            
            # Test message processing
            try:
                response = support_chatbot.process_message(session_id, "Test message")
                if not response or 'message' not in response:
                    issues.append("Chat message processing failed")
                    print("❌ Chat message processing failed")
                else:
                    print("✅ Chat message processing working")
            except Exception as e:
                issues.append(f"Chat message processing error: {e}")
                print(f"❌ Chat message processing error: {e}")
            
            # Test chat history
            try:
                history = support_chatbot.get_chat_history(session_id)
                print(f"✅ Chat history retrieved: {len(history)} messages")
            except Exception as e:
                issues.append(f"Chat history retrieval failed: {e}")
                print(f"❌ Chat history retrieval failed: {e}")
        
    except Exception as e:
        error = f"Chat system import/init failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_authentication_system():
    """Test authentication system"""
    print("\n🔍 TESTING AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        from auth_decorators import login_required, get_current_user
        from user_auth import user_manager
        
        print("✅ Auth decorators imported")
        print("✅ User manager imported")
        
        # Test user manager basic functionality
        try:
            # This might fail if no users exist, but should not crash
            result = user_manager.get_user_by_id(1)
            print("✅ User lookup working")
        except Exception as e:
            # This is not necessarily an error if user doesn't exist
            print(f"ℹ️ User lookup test: {e}")
        
    except Exception as e:
        error = f"Authentication system import failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_news_aggregation():
    """Test news aggregation system"""
    print("\n🔍 TESTING NEWS AGGREGATION")
    print("=" * 50)
    
    issues = []
    
    try:
        import news_aggregator
        print("✅ News aggregator imported")
        
        # Check if articles table has data
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        if article_count == 0:
            issues.append("No articles in database")
            print("⚠️ No articles in database (may need aggregation run)")
        else:
            print(f"✅ {article_count} articles in database")
        
        # Check recent articles
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-1 day')")
        recent_count = cursor.fetchone()[0]
        print(f"ℹ️ {recent_count} articles from last 24 hours")
        
        conn.close()
        
    except Exception as e:
        error = f"News aggregation test failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_live_events_system():
    """Test live events system"""
    print("\n🔍 TESTING LIVE EVENTS SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        import live_events_manager
        print("✅ Live events manager imported")
        
        # Check live events table
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'active'")
        active_events = cursor.fetchone()[0]
        print(f"ℹ️ {active_events} active live events")
        
        cursor.execute("SELECT COUNT(*) FROM live_events")
        total_events = cursor.fetchone()[0]
        print(f"ℹ️ {total_events} total live events")
        
        conn.close()
        
    except Exception as e:
        error = f"Live events test failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_api_functionality():
    """Test API functionality"""
    print("\n🔍 TESTING API FUNCTIONALITY")
    print("=" * 50)
    
    issues = []
    
    try:
        # Check API key management
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM api_keys")
        api_key_count = cursor.fetchone()[0]
        print(f"ℹ️ {api_key_count} API keys in database")
        
        # Check API usage tracking
        cursor.execute("SELECT COUNT(*) FROM api_usage")
        usage_count = cursor.fetchone()[0]
        print(f"ℹ️ {usage_count} API usage records")
        
        conn.close()
        print("✅ API tables accessible")
        
    except Exception as e:
        error = f"API functionality test failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_social_media_system():
    """Test social media system"""
    print("\n🔍 TESTING SOCIAL MEDIA SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        import social_media_manager
        print("✅ Social media manager imported")
        
        # Check social media tables
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM social_media_posts")
        posts_count = cursor.fetchone()[0]
        print(f"ℹ️ {posts_count} social media posts")
        
        conn.close()
        
    except Exception as e:
        error = f"Social media test failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_notification_system():
    """Test notification system"""
    print("\n🔍 TESTING NOTIFICATION SYSTEM")
    print("=" * 50)
    
    issues = []
    
    try:
        import notification_manager
        print("✅ Notification manager imported")
        
        # Check notification tables
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM notifications")
        notifications_count = cursor.fetchone()[0]
        print(f"ℹ️ {notifications_count} notifications in database")
        
        conn.close()
        
    except Exception as e:
        error = f"Notification system test failed: {e}"
        issues.append(error)
        print(f"❌ {error}")
    
    return len(issues) == 0, issues

def test_template_integrity():
    """Test template files integrity"""
    print("\n🔍 TESTING TEMPLATE INTEGRITY")
    print("=" * 50)
    
    issues = []
    
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        issues.append("Templates directory missing")
        print("❌ Templates directory missing")
        return False, issues
    
    critical_templates = [
        'index.html', 'dashboard.html', 'login.html', 'register.html',
        'subscription_plans.html', 'chat_interface.html', 'support_center.html',
        'article.html', 'live_feeds.html'
    ]
    
    for template in critical_templates:
        template_path = os.path.join(template_dir, template)
        if not os.path.exists(template_path):
            issues.append(f"Missing template: {template}")
            print(f"❌ Missing template: {template}")
        else:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 100:
                        issues.append(f"Template {template} seems too small")
                        print(f"⚠️ Template {template} seems too small")
                    else:
                        print(f"✅ Template {template} OK")
            except Exception as e:
                issues.append(f"Error reading template {template}: {e}")
                print(f"❌ Error reading template {template}: {e}")
    
    return len(issues) == 0, issues

def test_static_files():
    """Test static files integrity"""
    print("\n🔍 TESTING STATIC FILES")
    print("=" * 50)
    
    issues = []
    
    static_dir = 'static'
    if not os.path.exists(static_dir):
        issues.append("Static directory missing")
        print("❌ Static directory missing")
        return False, issues
    
    # Count static files
    static_files = []
    for root, dirs, files in os.walk(static_dir):
        static_files.extend(files)
    
    print(f"ℹ️ {len(static_files)} static files found")
    
    # Check for critical static files
    critical_files = ['icon-192.png', 'icon-512.png']
    for file in critical_files:
        file_path = os.path.join(static_dir, file)
        if os.path.exists(file_path):
            print(f"✅ Critical file {file} exists")
        else:
            print(f"⚠️ Critical file {file} missing")
    
    return len(issues) == 0, issues

def run_comprehensive_check():
    """Run all tests and provide comprehensive report"""
    print("🚀 COMPREHENSIVE SYSTEM CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print("=" * 60)
    
    test_functions = [
        ("Database Integrity", test_database_integrity),
        ("Core Imports", test_core_imports),
        ("Subscription System", test_subscription_system),
        ("Chat System", test_chat_system),
        ("Authentication System", test_authentication_system),
        ("News Aggregation", test_news_aggregation),
        ("Live Events System", test_live_events_system),
        ("API Functionality", test_api_functionality),
        ("Social Media System", test_social_media_system),
        ("Notification System", test_notification_system),
        ("Template Integrity", test_template_integrity),
        ("Static Files", test_static_files),
    ]
    
    all_results = {}
    all_issues = []
    
    for test_name, test_func in test_functions:
        try:
            success, issues = test_func()
            all_results[test_name] = success
            if issues:
                all_issues.extend([f"{test_name}: {issue}" for issue in issues])
        except Exception as e:
            all_results[test_name] = False
            error = f"{test_name}: Test crashed - {e}"
            all_issues.append(error)
            print(f"\n❌ {error}")
            traceback.print_exc()
    
    # Generate final report
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE SYSTEM REPORT")
    print("=" * 60)
    
    passed_tests = sum(1 for result in all_results.values() if result)
    total_tests = len(all_results)
    
    for test_name, success in all_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall System Health: {passed_tests}/{total_tests} systems OK")
    
    if all_issues:
        print(f"\n🚨 IDENTIFIED ISSUES ({len(all_issues)}):")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n💡 RECOMMENDED ACTIONS:")
        
        # Group issues by type
        db_issues = [issue for issue in all_issues if 'database' in issue.lower() or 'sql' in issue.lower()]
        import_issues = [issue for issue in all_issues if 'import' in issue.lower() or 'module' in issue.lower()]
        template_issues = [issue for issue in all_issues if 'template' in issue.lower()]
        
        if db_issues:
            print("   🗃️ Database Issues:")
            print("     - Run database repair/optimization")
            print("     - Check database permissions")
            print("     - Verify table schemas")
        
        if import_issues:
            print("   📦 Import Issues:")
            print("     - Check Python path")
            print("     - Verify module dependencies")
            print("     - Install missing packages")
        
        if template_issues:
            print("   🎨 Template Issues:")
            print("     - Restore missing templates")
            print("     - Check template syntax")
            print("     - Verify template variables")
        
    else:
        print("\n🎉 EXCELLENT! No issues detected!")
        print("   All systems are functioning correctly.")
    
    # Save report to file
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': all_results,
        'issues': all_issues,
        'summary': {
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%"
        }
    }
    
    with open('system_check_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📝 Detailed report saved to: system_check_report.json")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_comprehensive_check()
    sys.exit(0 if success else 1)
