"""
QUICK SYSTEM CHECK: Identify any remaining issues
===============================================
"""

import sqlite3
from datetime import datetime
import os

def quick_system_check():
    print('🔍 QUICK SYSTEM CHECK')
    print('=' * 50)
    
    issues_found = []
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # 1. Check database integrity
        print('1. 📊 Database Integrity Check:')
        cursor.execute('PRAGMA integrity_check')
        integrity = cursor.fetchone()[0]
        if integrity == 'ok':
            print('   ✅ Database integrity: OK')
        else:
            print(f'   ❌ Database integrity: {integrity}')
            issues_found.append('Database integrity issues')
        
        # 2. Check subscription plans configuration
        print('\n2. 📋 Subscription Plans Check:')
        cursor.execute('SELECT name, max_articles_per_day, max_searches_per_day FROM subscription_plans WHERE is_active = 1')
        plans = cursor.fetchall()
        
        plan_issues = []
        for name, max_articles, max_searches in plans:
            if name == 'free' and max_articles != 10:
                plan_issues.append(f'Free plan should have 10 articles, has {max_articles}')
            elif name in ['standard', 'premium'] and max_articles != -1:
                plan_issues.append(f'{name.title()} plan should have unlimited articles (-1), has {max_articles}')
        
        if plan_issues:
            for issue in plan_issues:
                print(f'   ❌ {issue}')
                issues_found.append(issue)
        else:
            print('   ✅ All subscription plans configured correctly')
        
        # 3. Check active subscriptions
        print('\n3. 👥 Active Subscriptions Check:')
        cursor.execute('''
            SELECT COUNT(*), sp.name 
            FROM user_subscriptions us 
            JOIN subscription_plans sp ON us.plan_id = sp.id 
            WHERE us.status IN ('active', 'trial') 
            GROUP BY sp.name
        ''')
        active_subs = cursor.fetchall()
        
        if active_subs:
            for count, plan_name in active_subs:
                print(f'   ✅ {count} active {plan_name} subscription(s)')
        else:
            print('   ⚠️  No active subscriptions found')
            issues_found.append('No active subscriptions')
        
        # 4. Check for expired trials
        print('\n4. ⏰ Trial Expiration Check:')
        today = datetime.now().date()
        cursor.execute('''
            SELECT user_id, trial_end_date 
            FROM user_subscriptions 
            WHERE status = 'trial' AND trial_end_date < ?
        ''', (today,))
        expired_trials = cursor.fetchall()
        
        if expired_trials:
            print(f'   ⚠️  {len(expired_trials)} expired trial(s) found')
            for user_id, end_date in expired_trials:
                print(f'      User {user_id}: Expired on {end_date}')
            issues_found.append(f'{len(expired_trials)} expired trials need cleanup')
        else:
            print('   ✅ No expired trials found')
        
        # 5. Check usage tracking data
        print('\n5. 📈 Usage Tracking Check:')
        cursor.execute('SELECT COUNT(*) FROM usage_tracking WHERE date = ?', (today,))
        usage_count = cursor.fetchone()[0]
        
        if usage_count > 0:
            print(f'   ✅ {usage_count} usage tracking entries for today')
        else:
            print('   ℹ️  No usage tracking data for today (normal if no activity)')
        
        # 6. Check for orphaned data
        print('\n6. 🧹 Data Consistency Check:')
        cursor.execute('''
            SELECT COUNT(*) 
            FROM user_subscriptions us 
            LEFT JOIN subscription_plans sp ON us.plan_id = sp.id 
            WHERE sp.id IS NULL
        ''')
        orphaned_subs = cursor.fetchone()[0]
        
        if orphaned_subs > 0:
            print(f'   ❌ {orphaned_subs} subscription(s) reference non-existent plans')
            issues_found.append(f'{orphaned_subs} orphaned subscriptions')
        else:
            print('   ✅ All subscriptions reference valid plans')
        
        conn.close()
        
        # 7. Check important files
        print('\n7. 📁 Critical Files Check:')
        critical_files = [
            'app.py',
            'subscription_manager.py', 
            'news_database.db',
            'requirements.txt'
        ]
        
        for file in critical_files:
            if os.path.exists(file):
                file_size = os.path.getsize(file)
                if file_size > 0:
                    print(f'   ✅ {file}: {file_size} bytes')
                else:
                    print(f'   ⚠️  {file}: Empty file')
                    issues_found.append(f'{file} is empty')
            else:
                print(f'   ❌ {file}: Missing')
                issues_found.append(f'{file} is missing')
        
        # Final summary
        print('\n' + '=' * 50)
        if not issues_found:
            print('🎉 SYSTEM STATUS: ALL GOOD!')
            print('✅ No issues found - system is ready for production')
        else:
            print(f'⚠️  ISSUES FOUND: {len(issues_found)}')
            for i, issue in enumerate(issues_found, 1):
                print(f'   {i}. {issue}')
            print('\n🔧 Recommendation: Address these issues before going live')
        
    except Exception as e:
        print(f'❌ Error during system check: {e}')
        issues_found.append(f'System check error: {e}')
    
    return issues_found

if __name__ == "__main__":
    quick_system_check()
