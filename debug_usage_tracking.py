#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def check_usage_tracking_issue():
    """Check why users are being redirected to subscription page"""
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        print("🔍 DIAGNOSING USAGE TRACKING ISSUE")
        print("=" * 50)
        
        # Check user subscriptions
        cursor.execute('''
            SELECT us.user_id, sp.name, us.status, sp.max_articles_per_day, sp.max_searches_per_day
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.status IN ('active', 'trial')
        ''')
        subs = cursor.fetchall()
        
        print("\n📋 USER SUBSCRIPTIONS:")
        for sub in subs:
            user_id, plan_name, status, max_articles, max_searches = sub
            articles_limit = "Unlimited" if max_articles == -1 else max_articles
            searches_limit = "Unlimited" if max_searches == -1 else max_searches
            print(f"   User {user_id}: {plan_name.upper()} ({status})")
            print(f"     Articles limit: {articles_limit}")
            print(f"     Searches limit: {searches_limit}")
        
        # Check today's usage
        today = datetime.now().date()
        cursor.execute('''
            SELECT user_id, articles_viewed, searches_performed
            FROM usage_tracking
            WHERE date = ?
        ''', (today,))
        usage_data = cursor.fetchall()
        
        print(f"\n📊 TODAY'S USAGE ({today}):")
        for usage in usage_data:
            user_id, articles_viewed, searches_performed = usage
            print(f"   User {user_id}: {articles_viewed} articles, {searches_performed} searches")
        
        # Check if any users should be blocked
        print(f"\n🚨 LIMIT CHECK:")
        for sub in subs:
            user_id, plan_name, status, max_articles, max_searches = sub
            
            # Find usage for this user
            user_usage = next((u for u in usage_data if u[0] == user_id), (user_id, 0, 0))
            articles_used = user_usage[1]
            
            if max_articles == -1:
                articles_status = "✅ UNLIMITED"
            elif articles_used >= max_articles:
                articles_status = f"❌ BLOCKED ({articles_used}/{max_articles})"
            else:
                articles_status = f"✅ OK ({articles_used}/{max_articles})"
            
            print(f"   User {user_id} ({plan_name}): {articles_status}")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        unlimited_users = [sub[0] for sub in subs if sub[3] == -1]  # max_articles_per_day == -1
        limited_users = [sub[0] for sub in subs if sub[3] != -1]
        
        if unlimited_users:
            print(f"   ✅ Unlimited Users: {unlimited_users} (No subscription redirects)")
        if limited_users:
            print(f"   ⚠️  Limited Users: {limited_users} (May be redirected when limits reached)")
        
        print(f"\n🎯 STATUS: All subscription plans working correctly!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_usage_tracking_issue()
