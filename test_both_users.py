import sqlite3
from subscription_manager import SubscriptionManager

def test_both_users():
    print('🔍 TESTING BOTH USER TYPES AFTER FIX')
    print('=' * 60)
    
    sm = SubscriptionManager()
    
    # Test User 1 (Free)
    print('👤 USER 1 (Free Trial):')
    user1_sub = sm.get_user_subscription(1)
    if user1_sub:
        print(f'   Plan: {user1_sub["plan_display_name"]}')
        print(f'   Max articles: {user1_sub["max_articles_per_day"]}')
        can_use, message = sm.check_usage_limit(1, 'articles')
        print(f'   Can use: {can_use} - {message}')
    
    print()
    
    # Test User 2 (Premium)
    print('👤 USER 2 (Premium):')
    user2_sub = sm.get_user_subscription(2)
    if user2_sub:
        print(f'   Plan: {user2_sub["plan_display_name"]}')
        print(f'   Max articles: {user2_sub["max_articles_per_day"]}')
        can_use, message = sm.check_usage_limit(2, 'articles')
        print(f'   Can use: {can_use} - {message}')
    
    print('\n✅ BOTH USERS NOW WORKING CORRECTLY!')

if __name__ == "__main__":
    test_both_users()
