#!/usr/bin/env python3
"""Clean up duplicate live events and maintain only the most recent ones."""

import sqlite3
from datetime import datetime, timedelta

def clean_duplicate_live_events():
    """Remove duplicate live events and keep only recent ones."""
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    try:
        print("🧹 Starting live events cleanup...")
        
        # 1. Get duplicate event names
        cursor.execute('''
            SELECT event_name, COUNT(*) as count 
            FROM live_events 
            GROUP BY event_name 
            HAVING count > 1 
            ORDER BY count DESC
        ''')
        duplicates = cursor.fetchall()
        
        print(f"Found {len(duplicates)} duplicate event types")
        
        total_removed = 0
        
        for event_name, count in duplicates:
            print(f"Processing '{event_name}' with {count} duplicates...")
            
            # Keep only the most recent event for each name
            cursor.execute('''
                SELECT id FROM live_events 
                WHERE event_name = ? 
                ORDER BY start_time DESC, id DESC
                LIMIT 1
            ''', (event_name,))
            
            keep_event = cursor.fetchone()
            if keep_event:
                keep_id = keep_event[0]
                
                # Delete all other instances of this event
                cursor.execute('''
                    DELETE FROM live_events 
                    WHERE event_name = ? AND id != ?
                ''', (event_name, keep_id))
                
                removed = cursor.rowcount
                total_removed += removed
                print(f"  ✅ Kept event ID {keep_id}, removed {removed} duplicates")
        
        # 2. Clean up old events (older than 5 minutes and still active)
        print("\n🕐 Cleaning up old active events...")
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        cursor.execute('''
            UPDATE live_events 
            SET status = 'completed' 
            WHERE start_time < ? 
            AND status = 'active'
        ''', (five_minutes_ago.isoformat(),))
        
        old_events_updated = cursor.rowcount
        print(f"  ✅ Marked {old_events_updated} old events as completed")
        
        # 3. Remove orphaned event updates
        print("\n🗑️ Cleaning up orphaned event updates...")
        cursor.execute('''
            DELETE FROM live_event_updates 
            WHERE event_id NOT IN (SELECT id FROM live_events)
        ''')
        
        orphaned_updates = cursor.rowcount
        print(f"  ✅ Removed {orphaned_updates} orphaned event updates")
        
        conn.commit()
        
        # 4. Show final stats
        print("\n📊 Final statistics:")
        cursor.execute('SELECT COUNT(*) FROM live_events')
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'active'")
        active_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'completed'")
        completed_events = cursor.fetchone()[0]
        
        print(f"  Total events: {total_events}")
        print(f"  Active events: {active_events}")
        print(f"  Completed events: {completed_events}")
        print(f"  Total duplicates removed: {total_removed}")
        print(f"  Old events marked completed: {old_events_updated}")
        print(f"  Orphaned updates removed: {orphaned_updates}")
        
        print("\n✅ Live events cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    clean_duplicate_live_events()
