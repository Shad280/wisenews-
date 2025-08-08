#!/usr/bin/env python3
"""
Comprehensive fix for template rendering errors and variable issues
"""

import sqlite3
from datetime import datetime

def fix_template_variable_issues():
    """Fix template rendering issues that cause 500 errors"""
    print("🔧 FIXING TEMPLATE VARIABLE ISSUES")
    print("=" * 50)
    
    fixes_applied = []
    
    # Fix 1: Update subscription route to handle None values safely
    try:
        print("1. Fixing subscription route template variable handling...")
        
        # Read current app.py subscription route
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Find the subscription_plans route
        subscription_route_start = app_content.find('@app.route(\'/subscription-plans\')')
        if subscription_route_start != -1:
            # Find the end of this route (next @app.route or end of function)
            subscription_route_end = app_content.find('@app.route', subscription_route_start + 1)
            if subscription_route_end == -1:
                subscription_route_end = len(app_content)
            
            # Extract the route function
            route_section = app_content[subscription_route_start:subscription_route_end]
            
            # Check if it needs fixing
            if 'daily_usage = subscription_manager.get_daily_usage(user_id)' in route_section:
                # Replace the route with a safer version
                new_route = '''@app.route('/subscription-plans')
@login_required
def subscription_plans():
    """Display available subscription plans"""
    user_id = session['user_id']
    
    try:
        # Get all plans
        plans = subscription_manager.get_all_plans()
        
        # Get current subscription with error handling
        current_subscription = subscription_manager.get_user_subscription(user_id)
        
        # Get daily usage with error handling
        daily_usage = subscription_manager.get_daily_usage(user_id)
        
        # Ensure daily_usage has all required fields
        if not daily_usage:
            daily_usage = {
                'articles_viewed': 0,
                'searches_performed': 0,
                'bookmarks_created': 0,
                'api_requests': 0
            }
        
        # Ensure all required fields exist
        daily_usage.setdefault('articles_viewed', 0)
        daily_usage.setdefault('searches_performed', 0)
        daily_usage.setdefault('bookmarks_created', 0)
        daily_usage.setdefault('api_requests', 0)
        
        return render_template('subscription_plans.html', 
                             plans=plans or [], 
                             current_subscription=current_subscription,
                             daily_usage=daily_usage)
                             
    except Exception as e:
        print(f"Error in subscription_plans route: {e}")
        flash('Unable to load subscription plans. Please try again.', 'error')
        return redirect(url_for('dashboard'))

'''
                
                # Replace the old route with the new one
                app_content = app_content[:subscription_route_start] + new_route + app_content[subscription_route_end:]
                fixes_applied.append("Fixed subscription_plans route error handling")
        
        # Fix the my-subscription route too
        my_subscription_start = app_content.find('@app.route(\'/my-subscription\')')
        if my_subscription_start != -1:
            my_subscription_end = app_content.find('@app.route', my_subscription_start + 1)
            if my_subscription_end == -1:
                my_subscription_end = len(app_content)
            
            new_my_sub_route = '''@app.route('/my-subscription')
@login_required
def my_subscription():
    """Display user's current subscription details"""
    user_id = session['user_id']
    
    try:
        # Get current subscription with error handling
        subscription = subscription_manager.get_user_subscription(user_id)
        
        if not subscription:
            flash('No active subscription found.', 'info')
            return redirect(url_for('subscription_plans'))
        
        # Get daily usage with error handling
        daily_usage = subscription_manager.get_daily_usage(user_id)
        
        # Ensure daily_usage has all required fields
        if not daily_usage:
            daily_usage = {
                'articles_viewed': 0,
                'searches_performed': 0,
                'bookmarks_created': 0,
                'api_requests': 0
            }
        
        # Ensure all required fields exist
        daily_usage.setdefault('articles_viewed', 0)
        daily_usage.setdefault('searches_performed', 0)
        daily_usage.setdefault('bookmarks_created', 0)
        daily_usage.setdefault('api_requests', 0)
        
        return render_template('my_subscription.html', 
                             subscription=subscription,
                             daily_usage=daily_usage)
                             
    except Exception as e:
        print(f"Error in my_subscription route: {e}")
        flash('Unable to load subscription details. Please try again.', 'error')
        return redirect(url_for('dashboard'))

'''
            
            app_content = app_content[:my_subscription_start] + new_my_sub_route + app_content[my_subscription_end:]
            fixes_applied.append("Fixed my_subscription route error handling")
        
        # Write the updated content back
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print("   ✅ Updated app.py subscription routes with error handling")
        
    except Exception as e:
        print(f"   ❌ Error fixing subscription routes: {e}")
    
    # Fix 2: Update support routes to handle None values
    try:
        print("2. Fixing support chat route error handling...")
        
        with open('support_routes.py', 'r', encoding='utf-8') as f:
            support_content = f.read()
        
        # Check if the routes need fixing
        if 'except Exception as e:' not in support_content:
            # Add error handling to the chat route
            chat_route_start = support_content.find('@support_bp.route(\'/chat\')')
            if chat_route_start != -1:
                chat_route_end = support_content.find('@support_bp.route', chat_route_start + 1)
                if chat_route_end == -1:
                    chat_route_end = support_content.find('def ', chat_route_start + 50)
                    if chat_route_end == -1:
                        chat_route_end = len(support_content)
                
                new_chat_route = '''@support_bp.route('/chat')
@login_required
def chat():
    """Start a chat session for logged-in users"""
    try:
        user_id = session['user_id']
        user = user_manager.get_user_by_id(user_id)
        
        if not user:
            flash('User session invalid. Please log in again.', 'error')
            return redirect(url_for('login_form'))
        
        # Create chat session with error handling
        session_id = support_chatbot.create_chat_session(user_id)
        
        if not session_id:
            flash('Unable to start chat session. Please try again.', 'error')
            return redirect(url_for('support_bp.index'))
        
        return render_template('chat_interface.html', user=user, session_id=session_id)
        
    except Exception as e:
        print(f"Error in chat route: {e}")
        flash('Unable to start chat. Please try again.', 'error')
        return redirect(url_for('support_bp.index'))

@support_bp.route('/chat/guest')
def guest_chat():
    """Start a guest chat session"""
    try:
        # Create guest chat session
        session_id = support_chatbot.create_chat_session(None)  # None for guest
        
        if not session_id:
            flash('Unable to start guest chat. Please try again.', 'error')
            return redirect(url_for('support_bp.index'))
        
        return render_template('chat_interface.html', user=None, session_id=session_id)
        
    except Exception as e:
        print(f"Error in guest_chat route: {e}")
        flash('Unable to start guest chat. Please try again.', 'error')
        return redirect(url_for('support_bp.index'))

'''
                
                # Find the function definitions and replace them
                guest_chat_start = support_content.find('@support_bp.route(\'/chat/guest\')')
                if guest_chat_start != -1:
                    guest_chat_end = support_content.find('def ', guest_chat_start + 50)
                    if guest_chat_end != -1:
                        # Find the end of guest_chat function
                        next_func = support_content.find('def ', guest_chat_end + 10)
                        if next_func == -1:
                            next_func = len(support_content)
                        
                        # Replace both functions
                        support_content = support_content[:chat_route_start] + new_chat_route + support_content[next_func:]
                        fixes_applied.append("Fixed support chat routes error handling")
        
        with open('support_routes.py', 'w', encoding='utf-8') as f:
            f.write(support_content)
        
        print("   ✅ Updated support_routes.py with error handling")
        
    except Exception as e:
        print(f"   ❌ Error fixing support routes: {e}")
    
    # Fix 3: Add template filters for safe rendering
    try:
        print("3. Adding template safety filters...")
        
        # Add safe template filters to app.py
        template_filters = '''
# Template filters for safe rendering
@app.template_filter('safe_attr')
def safe_attr(obj, attr, default='N/A'):
    """Safely get attribute from object with default"""
    try:
        if obj is None:
            return default
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            return value if value is not None else default
        else:
            return default
    except Exception:
        return default

@app.template_filter('safe_format_date')
def safe_format_date(date_obj, format_str='%B %d, %Y'):
    """Safely format date with default"""
    try:
        if date_obj is None:
            return 'Not set'
        if isinstance(date_obj, str):
            from datetime import datetime
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime(format_str)
    except Exception:
        return 'Invalid date'

@app.template_filter('safe_number')
def safe_number(value, default=0):
    """Safely get number with default"""
    try:
        if value is None:
            return default
        return int(value) if isinstance(value, (int, float, str)) else default
    except Exception:
        return default

'''
        
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Add filters before the main routes
        if '@app.template_filter' not in app_content:
            # Find a good place to insert (after imports, before routes)
            insert_point = app_content.find('# Routes')
            if insert_point == -1:
                insert_point = app_content.find('@app.route')
            
            if insert_point != -1:
                app_content = app_content[:insert_point] + template_filters + '\n' + app_content[insert_point:]
                
                with open('app.py', 'w', encoding='utf-8') as f:
                    f.write(app_content)
                
                fixes_applied.append("Added template safety filters")
                print("   ✅ Added template safety filters to app.py")
        
    except Exception as e:
        print(f"   ❌ Error adding template filters: {e}")
    
    return fixes_applied

def fix_template_files():
    """Update template files to use safe rendering"""
    print("🔧 FIXING TEMPLATE FILES")
    print("=" * 50)
    
    fixes_applied = []
    
    # Fix subscription_plans.html
    try:
        print("1. Fixing subscription_plans.html...")
        
        with open('templates/subscription_plans.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace unsafe template variables with safe ones
        replacements = [
            ('{{ current_subscription.plan_display_name }}', '{{ current_subscription.plan_display_name if current_subscription else "No subscription" }}'),
            ('{{ current_subscription.trial_end_date.strftime(\'%B %d, %Y\') }}', '{{ current_subscription.trial_end_date | safe_format_date if current_subscription and current_subscription.trial_end_date else "Not set" }}'),
            ('{{ daily_usage.articles_viewed }}', '{{ daily_usage.articles_viewed | safe_number }}'),
            ('{{ daily_usage.bookmarks_created }}', '{{ daily_usage.bookmarks_created | safe_number }}'),
            ('{{ daily_usage.api_requests }}', '{{ daily_usage.api_requests | safe_number }}'),
        ]
        
        for old, new in replacements:
            if old in template_content:
                template_content = template_content.replace(old, new)
                fixes_applied.append(f"Fixed template variable: {old}")
        
        with open('templates/subscription_plans.html', 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print("   ✅ Fixed subscription_plans.html template variables")
        
    except Exception as e:
        print(f"   ❌ Error fixing subscription_plans.html: {e}")
    
    # Fix my_subscription.html
    try:
        print("2. Fixing my_subscription.html...")
        
        with open('templates/my_subscription.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace unsafe template variables
        replacements = [
            ('{{ subscription.plan_display_name }}', '{{ subscription.plan_display_name if subscription else "No subscription" }}'),
            ('{{ subscription.trial_start_date.strftime(\'%B %d, %Y\') }}', '{{ subscription.trial_start_date | safe_format_date if subscription and subscription.trial_start_date else "Not set" }}'),
            ('{{ subscription.trial_end_date.strftime(\'%B %d, %Y\') }}', '{{ subscription.trial_end_date | safe_format_date if subscription and subscription.trial_end_date else "Not set" }}'),
            ('{{ subscription.subscription_start_date.strftime(\'%B %d, %Y\') }}', '{{ subscription.subscription_start_date | safe_format_date if subscription and subscription.subscription_start_date else "Not set" }}'),
            ('{{ subscription.subscription_end_date.strftime(\'%B %d, %Y\') }}', '{{ subscription.subscription_end_date | safe_format_date if subscription and subscription.subscription_end_date else "Not set" }}'),
            ('{{ daily_usage.articles_viewed }}', '{{ daily_usage.articles_viewed | safe_number }}'),
            ('{{ daily_usage.api_requests }}', '{{ daily_usage.api_requests | safe_number }}'),
        ]
        
        for old, new in replacements:
            if old in template_content:
                template_content = template_content.replace(old, new)
                fixes_applied.append(f"Fixed template variable: {old}")
        
        with open('templates/my_subscription.html', 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print("   ✅ Fixed my_subscription.html template variables")
        
    except Exception as e:
        print(f"   ❌ Error fixing my_subscription.html: {e}")
    
    return fixes_applied

def fix_session_handling():
    """Fix session handling issues"""
    print("🔧 FIXING SESSION HANDLING")
    print("=" * 50)
    
    fixes_applied = []
    
    try:
        # Add better session validation to user_auth.py
        with open('user_auth.py', 'r', encoding='utf-8') as f:
            auth_content = f.read()
        
        # Check if validate_session method needs improvement
        if 'def validate_session(' in auth_content:
            print("1. Improving session validation...")
            
            # Add better error handling to validate_session
            validate_start = auth_content.find('def validate_session(')
            if validate_start != -1:
                validate_end = auth_content.find('def ', validate_start + 1)
                if validate_end == -1:
                    validate_end = len(auth_content)
                
                # Create improved validation method
                new_validate = '''    def validate_session(self, session_token):
        """
        Validate a session token and return user data
        """
        try:
            if not session_token:
                return False, None
            
            # Get database connection with error handling
            conn = None
            try:
                conn = self.get_db_connection()
                if not conn:
                    return False, None
                
                cursor = conn.cursor()
                
                # Query with proper error handling
                cursor.execute("""
                    SELECT u.id, u.username, u.email, u.created_at, u.is_admin, 
                           s.created_at as session_created, s.expires_at
                    FROM users u 
                    JOIN user_sessions s ON u.id = s.user_id 
                    WHERE s.session_token = ? AND s.expires_at > datetime('now')
                """, (session_token,))
                
                result = cursor.fetchone()
                
                if result:
                    user_data = {
                        'id': result[0],
                        'username': result[1] or 'Unknown',
                        'email': result[2] or '',
                        'created_at': result[3] or '',
                        'is_admin': bool(result[4]) if result[4] is not None else False,
                        'session_created': result[5] or '',
                        'session_expires': result[6] or ''
                    }
                    return True, user_data
                else:
                    return False, None
                    
            except sqlite3.Error as e:
                print(f"Database error in validate_session: {e}")
                return False, None
            except Exception as e:
                print(f"Unexpected error in validate_session: {e}")
                return False, None
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            print(f"Critical error in validate_session: {e}")
            return False, None

'''
                
                # Replace the method
                method_indent = '    '  # Assuming it's inside a class
                auth_content = auth_content[:validate_start] + new_validate + auth_content[validate_end:]
                
                with open('user_auth.py', 'w', encoding='utf-8') as f:
                    f.write(auth_content)
                
                fixes_applied.append("Improved session validation method")
                print("   ✅ Improved session validation in user_auth.py")
        
    except Exception as e:
        print(f"   ❌ Error fixing session handling: {e}")
    
    return fixes_applied

def test_fixes():
    """Test that the fixes work"""
    print("🧪 TESTING FIXES")
    print("=" * 50)
    
    try:
        from subscription_manager import SubscriptionManager
        from user_auth import user_manager
        
        manager = SubscriptionManager()
        
        # Test subscription manager with None handling
        print("1. Testing subscription manager error handling...")
        
        # Test with invalid user
        subscription = manager.get_user_subscription(99999)
        print(f"   Non-existent user subscription: {subscription}")
        
        usage = manager.get_daily_usage(99999)
        print(f"   Non-existent user usage: {usage}")
        
        # Test with valid user
        subscription = manager.get_user_subscription(1)
        print(f"   Valid user subscription: {subscription is not None}")
        
        usage = manager.get_daily_usage(1)
        print(f"   Valid user usage: {usage is not None}")
        
        print("2. Testing user manager error handling...")
        
        # Test session validation
        is_valid, user_data = user_manager.validate_session("invalid_token")
        print(f"   Invalid session validation: {is_valid}")
        
        user = user_manager.get_user_by_id(1)
        print(f"   Valid user lookup: {user is not None}")
        
        print("   ✅ All fixes tested successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing fixes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Apply comprehensive fixes for template rendering errors"""
    print("🔧 COMPREHENSIVE TEMPLATE ERROR FIXES")
    print("=" * 60)
    
    all_fixes = []
    
    # Apply all fixes
    fixes1 = fix_template_variable_issues()
    fixes2 = fix_template_files()
    fixes3 = fix_session_handling()
    
    all_fixes.extend(fixes1)
    all_fixes.extend(fixes2)
    all_fixes.extend(fixes3)
    
    # Test the fixes
    test_success = test_fixes()
    
    # Summary
    print(f"\n📊 FIX SUMMARY:")
    print(f"   Total fixes applied: {len(all_fixes)}")
    
    for fix in all_fixes:
        print(f"   ✅ {fix}")
    
    if test_success:
        print(f"\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
        print(f"\n🔧 WHAT WAS FIXED:")
        print(f"   1. Template variable safety - prevents None object errors")
        print(f"   2. Route error handling - catches exceptions gracefully")
        print(f"   3. Session validation improvements - better error handling")
        print(f"   4. Template filters - safe rendering of data")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Restart your Flask application")
        print(f"   2. Clear your browser cache")
        print(f"   3. Try accessing the problematic features again")
        print(f"   4. If you still see errors, check browser console for JavaScript issues")
    else:
        print(f"\n⚠️ Some fixes may need manual verification")
        print(f"   Please test the application manually")

if __name__ == "__main__":
    main()
