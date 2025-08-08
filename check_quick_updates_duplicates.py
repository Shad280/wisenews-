import sqlite3

def check_quick_updates_duplicates():
    print('🔍 QUICK UPDATES DUPLICATE ANALYSIS')
    print('=' * 50)
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'📋 Available tables: {", ".join(tables)}')
        
        # Check notifications table
        if 'notifications' in tables:
            cursor.execute('SELECT COUNT(*) FROM notifications')
            total_notifications = cursor.fetchone()[0]
            print(f'\n📊 Total notifications: {total_notifications}')
            
            if total_notifications > 0:
                # Get all notifications for duplicate analysis
                cursor.execute('''
                    SELECT id, title, content, category, source_name, date_added, notification_type
                    FROM notifications 
                    ORDER BY date_added DESC
                ''')
                
                notifications = cursor.fetchall()
                
                # Check for duplicate titles
                seen_titles = {}
                duplicates_found = []
                
                for notif in notifications:
                    notif_id, title, content, category, source, date_added, ntype = notif
                    
                    if title:
                        # Normalize title for comparison
                        normalized_title = title.lower().strip()
                        
                        if normalized_title in seen_titles:
                            duplicates_found.append({
                                'title': title,
                                'first_occurrence': seen_titles[normalized_title],
                                'duplicate_id': notif_id,
                                'duplicate_date': date_added
                            })
                        else:
                            seen_titles[normalized_title] = {
                                'id': notif_id, 
                                'date': date_added,
                                'original_title': title
                            }
                
                if duplicates_found:
                    print(f'\n❌ DUPLICATE NOTIFICATIONS FOUND: {len(duplicates_found)}')
                    for dup in duplicates_found[:10]:  # Show first 10
                        print(f'   • "{dup["title"][:50]}..."')
                        print(f'     First: {dup["first_occurrence"]["date"]} (ID: {dup["first_occurrence"]["id"]})')
                        print(f'     Duplicate: {dup["duplicate_date"]} (ID: {dup["duplicate_id"]})')
                        print()
                else:
                    print(f'\n✅ No duplicate titles found')
                
                # Show recent notifications
                print(f'\n📋 RECENT NOTIFICATIONS (Last 10):')
                for i, notif in enumerate(notifications[:10], 1):
                    title = notif[1][:50] if notif[1] else 'No title'
                    category = notif[3] or 'Unknown'
                    date_added = notif[5]
                    print(f'   {i}. [{category}] {title}... ({date_added})')
            
        # Check live_event_updates for breaking news/live updates
        if 'live_event_updates' in tables:
            cursor.execute('SELECT COUNT(*) FROM live_event_updates')
            total_updates = cursor.fetchone()[0]
            print(f'\n📊 Total live event updates: {total_updates}')
            
            if total_updates > 0:
                cursor.execute('''
                    SELECT title, timestamp, importance 
                    FROM live_event_updates 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                ''')
                
                updates = cursor.fetchall()
                print(f'\n📋 RECENT LIVE UPDATES:')
                for i, update in enumerate(updates, 1):
                    title = update[0][:50] if update[0] else 'No title'
                    timestamp = update[1]
                    importance = update[2]
                    print(f'   {i}. {title}... (Importance: {importance}) ({timestamp})')
        
        conn.close()
        
        print(f'\n🎯 RECOMMENDATIONS:')
        if duplicates_found:
            print(f'   1. Remove {len(duplicates_found)} duplicate notifications')
            print(f'   2. Implement duplicate prevention in notification creation')
            print(f'   3. Add unique constraints to prevent future duplicates')
        else:
            print(f'   ✅ Quick updates are clean - no duplicates detected')
        
    except Exception as e:
        print(f'❌ Error analyzing quick updates: {e}')

if __name__ == "__main__":
    check_quick_updates_duplicates()
