import sqlite3
from subscription_manager import SubscriptionManager

def test_standard_users():
    print('🔍 TESTING STANDARD PLAN USERS')
    print('=' * 50)
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Check Standard plan configuration
    cursor.execute('SELECT * FROM subscription_plans WHERE name = "standard"')
    standard_plan = cursor.fetchone()
    
    if standard_plan:
        print('📋 STANDARD PLAN CONFIGURATION:')
        print(f'   Plan ID: {standard_plan[0]}')
        print(f'   Name: {standard_plan[1]}')
        print(f'   Display Name: {standard_plan[2]}')
        print(f'   Max Articles Per Day: {standard_plan[7]} {"(Unlimited)" if standard_plan[7] == -1 else ""}')
        print(f'   Max Searches Per Day: {standard_plan[8]} {"(Unlimited)" if standard_plan[8] == -1 else ""}')
        print(f'   Max Bookmarks: {standard_plan[9]} {"(Unlimited)" if standard_plan[9] == 50 else ""}')
    
    # Check for existing Standard users
    cursor.execute('''
        SELECT us.user_id, us.status 
        FROM user_subscriptions us 
        WHERE us.plan_id = 2 AND us.status IN ('active', 'trial')
    ''')
    standard_users = cursor.fetchall()
    
    print(f'\n👥 EXISTING STANDARD USERS: {len(standard_users)}')
    for user_id, status in standard_users:
        print(f'   User {user_id}: {status}')
    
    # If no Standard users exist, create a test scenario
    if not standard_users:
        print('\n🧪 CREATING TEST STANDARD USER...')
        
        # Check if we have a user we can upgrade to Standard
        cursor.execute('SELECT id FROM users ORDER BY id LIMIT 3')
        available_users = cursor.fetchall()
        
        if len(available_users) >= 3:
            test_user_id = available_users[2][0]  # Use third user for Standard test
            
            # Create Standard subscription for test user
            cursor.execute('''
                INSERT OR REPLACE INTO user_subscriptions 
                (user_id, plan_id, status, subscription_start_date, subscription_end_date, auto_renew)
                VALUES (?, 2, 'active', datetime('now'), '2026-12-31', 1)
            ''', (test_user_id,))
            
            conn.commit()
            print(f'   ✅ Created Standard subscription for User {test_user_id}')
            
            # Test the subscription
            sm = SubscriptionManager()
            subscription = sm.get_user_subscription(test_user_id)
            
            if subscription:
                print(f'\n✅ STANDARD USER TEST RESULTS:')
                print(f'   User ID: {test_user_id}')
                print(f'   Plan: {subscription["plan_display_name"]}')
                print(f'   Max Articles: {subscription["max_articles_per_day"]} {"(Unlimited)" if subscription["max_articles_per_day"] == -1 else ""}')
                print(f'   Max Searches: {subscription["max_searches_per_day"]} {"(Unlimited)" if subscription["max_searches_per_day"] == -1 else ""}')
                
                # Test usage limit check
                can_use, message = sm.check_usage_limit(test_user_id, 'articles')
                print(f'   Usage Check: {can_use} - {message}')
                
                if subscription["max_articles_per_day"] == -1 and can_use:
                    print('   ✅ PASS: Standard user has unlimited access')
                else:
                    print('   ❌ FAIL: Standard user should have unlimited access')
            else:
                print('   ❌ ERROR: Could not retrieve Standard subscription')
        else:
            print('   ❌ Not enough users to create test scenario')
    else:
        # Test existing Standard users
        sm = SubscriptionManager()
        for user_id, status in standard_users:
            print(f'\n✅ TESTING EXISTING STANDARD USER {user_id}:')
            subscription = sm.get_user_subscription(user_id)
            
            if subscription:
                print(f'   Plan: {subscription["plan_display_name"]}')
                print(f'   Max Articles: {subscription["max_articles_per_day"]} {"(Unlimited)" if subscription["max_articles_per_day"] == -1 else ""}')
                
                can_use, message = sm.check_usage_limit(user_id, 'articles')
                print(f'   Usage Check: {can_use} - {message}')
                
                if subscription["max_articles_per_day"] == -1 and can_use:
                    print('   ✅ PASS: Standard user has unlimited access')
                else:
                    print('   ❌ FAIL: Standard user should have unlimited access')
    
    # Summary
    print(f'\n📊 SUMMARY:')
    print(f'   • Standard plan should have unlimited articles (-1)')
    print(f'   • Standard users should not be redirected to subscription page')
    print(f'   • Both Standard and Premium should work identically for article access')
    
    conn.close()

if __name__ == "__main__":
    test_standard_users()
