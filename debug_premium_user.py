#!/usr/bin/env python3
"""
Debug subscription data structure for premium user
"""
import sys
sys.path.append('.')

from subscription_manager import SubscriptionManager

def debug_premium_user():
    """Debug what data is returned for premium user"""
    
    sm = SubscriptionManager()
    
    print("🔍 DEBUGGING PREMIUM USER SUBSCRIPTION DATA")
    print("=" * 60)
    
    # Check user 2 (premium user)
    user_id = 2
    
    subscription = sm.get_user_subscription(user_id)
    
    if subscription:
        print(f"\n📊 User {user_id} Subscription Data:")
        for key, value in subscription.items():
            print(f"   {key}: {value}")
        
        print(f"\n🔍 Key Limits Check:")
        print(f"   max_articles_per_day: {subscription.get('max_articles_per_day')} (type: {type(subscription.get('max_articles_per_day'))})")
        print(f"   max_searches_per_day: {subscription.get('max_searches_per_day')} (type: {type(subscription.get('max_searches_per_day'))})")
        
        # Test the limit check
        can_use, message = sm.check_usage_limit(user_id, 'articles_viewed')
        print(f"\n🧪 Limit Check Result:")
        print(f"   Can use: {can_use}")
        print(f"   Message: {message}")
        
        # Check today's usage
        usage = sm.get_daily_usage(user_id)
        print(f"\n📈 Today's Usage:")
        for key, value in usage.items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ No subscription found for user {user_id}")

if __name__ == "__main__":
    debug_premium_user()
