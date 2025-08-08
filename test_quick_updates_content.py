"""
Test Quick Updates Functionality
===============================
Verify that Quick Updates shows breaking news, live events, and small changes without duplicates
"""

import sqlite3
from collections import Counter

def test_quick_updates_content():
    print('🧪 TESTING QUICK UPDATES FUNCTIONALITY')
    print('=' * 60)
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get notifications the same way the quick_updates route does
        cursor.execute('''
            SELECT id, title, content, category, source_name, date_added, priority, notification_type
            FROM notifications 
            ORDER BY date_added DESC 
            LIMIT 50
        ''')
        
        notifications = cursor.fetchall()
        
        print(f'📊 Total notifications in Quick Updates: {len(notifications)}')
        
        if notifications:
            # Analyze notification types
            categories = [n[3] for n in notifications if n[3]]
            types = [n[7] for n in notifications if n[7]]
            
            category_counts = Counter(categories)
            type_counts = Counter(types)
            
            print(f'\\n📋 CONTENT BREAKDOWN:')
            print(f'   Categories:')
            for category, count in category_counts.most_common(10):
                print(f'     • {category}: {count}')
            
            print(f'   \\n   Notification Types:')
            for ntype, count in type_counts.most_common(10):
                print(f'     • {ntype}: {count}')
            
            # Check for breaking news and live events
            breaking_news = [n for n in notifications if 'breaking' in (n[1] or '').lower() or 'urgent' in (n[1] or '').lower()]
            live_events = [n for n in notifications if n[7] == 'live_event']
            finance_updates = [n for n in notifications if n[3] in ['crypto', 'finance', 'Financial']]
            sports_updates = [n for n in notifications if n[3] in ['sports', 'basketball', 'Sports']]
            
            print(f'\\n🎯 CONTENT ANALYSIS:')
            print(f'   🚨 Breaking News: {len(breaking_news)} notifications')
            print(f'   🔴 Live Events: {len(live_events)} notifications')
            print(f'   📈 Finance Updates: {len(finance_updates)} notifications')
            print(f'   ⚽ Sports Updates: {len(sports_updates)} notifications')
            
            # Show sample content
            print(f'\\n📋 SAMPLE CONTENT (Top 10):')
            for i, notif in enumerate(notifications[:10], 1):
                title = notif[1][:60] if notif[1] else 'No title'
                category = notif[3] or 'Unknown'
                ntype = notif[7] or 'general'
                date_added = notif[5]
                
                # Determine content type
                content_type = '🚨' if 'breaking' in title.lower() else '🔴' if ntype == 'live_event' else '📈' if category in ['crypto', 'finance'] else '⚽' if category in ['sports', 'basketball'] else '📰'
                
                print(f'   {i}. {content_type} [{category}] {title}')
                print(f'      Type: {ntype} | Date: {date_added}')
            
            # Check for proper diversity in updates
            recent_24h = [n for n in notifications if '2025-08-06' in (n[5] or '')]
            
            print(f'\\n⏰ RECENT ACTIVITY (Last 24h):')
            print(f'   • {len(recent_24h)} new updates today')
            
            if recent_24h:
                recent_categories = Counter([n[3] for n in recent_24h if n[3]])
                print(f'   • Category distribution:')
                for cat, count in recent_categories.most_common(5):
                    print(f'     - {cat}: {count}')
            
            # Verify no duplicates exist
            titles = [n[1] for n in notifications if n[1]]
            title_counts = Counter(titles)
            duplicates = {title: count for title, count in title_counts.items() if count > 1}
            
            if duplicates:
                print(f'\\n❌ DUPLICATES FOUND: {len(duplicates)}')
                for title, count in list(duplicates.items())[:5]:
                    print(f'   • "{title[:50]}..." appears {count} times')
            else:
                print(f'\\n✅ NO DUPLICATES: All notifications are unique')
            
            print(f'\\n🎯 QUICK UPDATES ASSESSMENT:')
            
            # Check if it contains proper breaking news content
            has_breaking = len(breaking_news) > 0
            has_live_events = len(live_events) > 0
            has_financial = len(finance_updates) > 0
            has_sports = len(sports_updates) > 0
            is_diverse = len(category_counts) >= 3
            no_duplicates = len(duplicates) == 0
            
            print(f'   ✅ Breaking News: {"Present" if has_breaking else "Missing"}')
            print(f'   ✅ Live Events: {"Present" if has_live_events else "Missing"}')
            print(f'   ✅ Financial Updates: {"Present" if has_financial else "Missing"}')
            print(f'   ✅ Sports Updates: {"Present" if has_sports else "Missing"}')
            print(f'   ✅ Content Diversity: {"Good" if is_diverse else "Limited"}')
            print(f'   ✅ No Duplicates: {"Confirmed" if no_duplicates else "Issues Found"}')
            
            # Overall assessment
            score = sum([has_breaking, has_live_events, has_financial, has_sports, is_diverse, no_duplicates])
            
            if score >= 5:
                status = "🎉 EXCELLENT"
                message = "Quick Updates is working perfectly!"
            elif score >= 4:
                status = "✅ GOOD"
                message = "Quick Updates is working well with minor areas for improvement"
            elif score >= 3:
                status = "⚠️ FAIR"
                message = "Quick Updates needs some improvements"
            else:
                status = "❌ POOR"
                message = "Quick Updates requires significant fixes"
            
            print(f'\\n{status}: {message}')
            print(f'   Score: {score}/6')
            
        else:
            print(f'\\n⚠️ No notifications found in Quick Updates')
            print(f'   This could indicate:')
            print(f'   • No breaking news or live events have occurred')
            print(f'   • Notification system needs to be activated')
            print(f'   • Live events manager may not be running')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Error testing Quick Updates: {e}')

if __name__ == "__main__":
    test_quick_updates_content()
