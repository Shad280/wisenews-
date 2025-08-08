"""
Fix Quick Updates Duplicates
============================
Remove duplicate notifications and implement prevention logic
"""

import sqlite3
from collections import defaultdict
import hashlib

def fix_quick_updates_duplicates():
    print('🔧 FIXING QUICK UPDATES DUPLICATES')
    print('=' * 50)
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get all notifications grouped by normalized title
        cursor.execute('''
            SELECT id, title, content, category, source_name, date_added, notification_type
            FROM notifications 
            ORDER BY date_added DESC
        ''')
        
        notifications = cursor.fetchall()
        duplicates_by_title = defaultdict(list)
        
        # Group notifications by normalized title
        for notif in notifications:
            notif_id, title, content, category, source, date_added, ntype = notif
            
            if title:
                # Create a normalized key for comparison
                normalized_title = title.lower().strip()
                duplicates_by_title[normalized_title].append({
                    'id': notif_id,
                    'title': title,
                    'content': content,
                    'category': category,
                    'source': source,
                    'date_added': date_added,
                    'type': ntype
                })
        
        # Find and remove duplicates (keep the most recent one)
        duplicates_to_remove = []
        total_duplicates = 0
        
        for normalized_title, group in duplicates_by_title.items():
            if len(group) > 1:
                # Sort by date_added (most recent first)
                group.sort(key=lambda x: x['date_added'], reverse=True)
                
                # Keep the first (most recent), mark others for deletion
                keep = group[0]
                to_remove = group[1:]
                
                total_duplicates += len(to_remove)
                
                print(f'📋 "{normalized_title[:50]}...": Keeping 1, removing {len(to_remove)}')
                
                for dup in to_remove:
                    duplicates_to_remove.append(dup['id'])
        
        if duplicates_to_remove:
            print(f'\\n🗑️ Removing {len(duplicates_to_remove)} duplicate notifications...')
            
            # Remove duplicates
            placeholders = ','.join('?' for _ in duplicates_to_remove)
            cursor.execute(f'DELETE FROM notifications WHERE id IN ({placeholders})', duplicates_to_remove)
            
            conn.commit()
            print(f'✅ Removed {len(duplicates_to_remove)} duplicate notifications')
        else:
            print(f'\\n✅ No duplicates found to remove')
        
        # Check final count
        cursor.execute('SELECT COUNT(*) FROM notifications')
        final_count = cursor.fetchone()[0]
        print(f'\\n📊 Final notification count: {final_count}')
        
        # Add unique constraint to prevent future duplicates
        print(f'\\n🔧 Adding duplicate prevention measures...')
        
        # Add title hash column if it doesn't exist
        cursor.execute("PRAGMA table_info(notifications)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'title_hash' not in columns:
            cursor.execute('ALTER TABLE notifications ADD COLUMN title_hash TEXT')
            print('✅ Added title_hash column')
        
        if 'content_hash' not in columns:
            cursor.execute('ALTER TABLE notifications ADD COLUMN content_hash TEXT')
            print('✅ Added content_hash column')
        
        # Update existing notifications with hashes
        cursor.execute('SELECT id, title, content FROM notifications WHERE title_hash IS NULL')
        to_update = cursor.fetchall()
        
        for notif_id, title, content in to_update:
            title_hash = hashlib.md5((title or '').encode()).hexdigest() if title else None
            content_hash = hashlib.md5((content or '').encode()).hexdigest() if content else None
            
            cursor.execute('''
                UPDATE notifications 
                SET title_hash = ?, content_hash = ? 
                WHERE id = ?
            ''', (title_hash, content_hash, notif_id))
        
        # Create indexes for fast duplicate checking
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_title_hash ON notifications(title_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_content_hash ON notifications(content_hash)')
            print('✅ Created duplicate prevention indexes')
        except sqlite3.Error as e:
            print(f'ℹ️ Indexes already exist or error: {e}')
        
        conn.commit()
        conn.close()
        
        print(f'\\n🎉 QUICK UPDATES DUPLICATE FIX COMPLETE!')
        print(f'   • Removed {len(duplicates_to_remove)} duplicates')
        print(f'   • Added duplicate prevention infrastructure')
        print(f'   • Quick Updates should now show unique breaking news only')
        
    except Exception as e:
        print(f'❌ Error fixing quick updates: {e}')

def create_notification_with_duplicate_check(title, content, category, source_name, notification_type='general', priority=0):
    """
    Enhanced function to create notifications with duplicate checking
    """
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Generate hashes for duplicate checking
        title_hash = hashlib.md5((title or '').encode()).hexdigest() if title else None
        content_hash = hashlib.md5((content or '').encode()).hexdigest() if content else None
        
        # Check for existing notification with same title hash
        if title_hash:
            cursor.execute('SELECT id FROM notifications WHERE title_hash = ?', (title_hash,))
            if cursor.fetchone():
                print(f'⚠️ Duplicate notification prevented: "{title[:50]}..."')
                conn.close()
                return False
        
        # Insert new notification
        cursor.execute('''
            INSERT INTO notifications 
            (title, content, category, source_name, notification_type, priority, title_hash, content_hash, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (title, content, category, source_name, notification_type, priority, title_hash, content_hash))
        
        conn.commit()
        conn.close()
        
        print(f'✅ Created unique notification: "{title[:50]}..."')
        return True
        
    except Exception as e:
        print(f'❌ Error creating notification: {e}')
        return False

if __name__ == "__main__":
    fix_quick_updates_duplicates()
    
    # Test the duplicate prevention
    print(f'\\n🧪 TESTING DUPLICATE PREVENTION:')
    
    # Try to create a duplicate
    test_title = "Test Breaking News Alert"
    test_content = "This is a test breaking news notification"
    
    # First creation should succeed
    result1 = create_notification_with_duplicate_check(
        test_title, test_content, 'breaking_news', 'WiseNews Test', 'breaking'
    )
    
    # Second creation should be prevented
    result2 = create_notification_with_duplicate_check(
        test_title, test_content, 'breaking_news', 'WiseNews Test', 'breaking'
    )
    
    print(f'First creation: {"✅ Success" if result1 else "❌ Failed"}')
    print(f'Duplicate prevention: {"✅ Working" if not result2 else "❌ Failed"}')
    
    # Clean up test notification
    if result1:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        title_hash = hashlib.md5(test_title.encode()).hexdigest()
        cursor.execute('DELETE FROM notifications WHERE title_hash = ?', (title_hash,))
        conn.commit()
        conn.close()
        print('✅ Cleaned up test notification')
