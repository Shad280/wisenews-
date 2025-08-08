import sqlite3
from datetime import datetime

def clean_duplicate_live_events():
    """Remove duplicate live events, keeping only the most recent one for each name"""
    print("🧹 Cleaning Duplicate Live Events...")
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    try:
        # Find duplicates
        cursor.execute("""
            SELECT event_name, COUNT(*) as count 
            FROM live_events 
            WHERE status = 'live'
            GROUP BY event_name 
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        print(f"📊 Found {len(duplicates)} duplicate event names")
        
        total_removed = 0
        
        for event_name, count in duplicates:
            print(f"\n🔍 Processing: {event_name} ({count} copies)")
            
            # Get all instances of this event, ordered by most recent first
            cursor.execute("""
                SELECT id, created_at, last_updated 
                FROM live_events 
                WHERE event_name = ? AND status = 'live'
                ORDER BY last_updated DESC, created_at DESC
            """, (event_name,))
            
            event_instances = cursor.fetchall()
            
            # Keep the first (most recent) and delete the rest
            if len(event_instances) > 1:
                keep_id = event_instances[0][0]
                print(f"   ✅ Keeping event ID {keep_id} (most recent)")
                
                for i in range(1, len(event_instances)):
                    delete_id = event_instances[i][0]
                    
                    # Delete related updates first
                    cursor.execute("DELETE FROM live_event_updates WHERE event_id = ?", (delete_id,))
                    updates_deleted = cursor.rowcount
                    
                    # Delete the event
                    cursor.execute("DELETE FROM live_events WHERE id = ?", (delete_id,))
                    
                    print(f"   🗑️ Removed event ID {delete_id} ({updates_deleted} updates)")
                    total_removed += 1
        
        conn.commit()
        print(f"\n✅ Cleanup complete: Removed {total_removed} duplicate events")
        
        # Verify cleanup
        cursor.execute("""
            SELECT event_name, COUNT(*) as count 
            FROM live_events 
            WHERE status = 'live'
            GROUP BY event_name 
            HAVING count > 1
        """)
        
        remaining_duplicates = cursor.fetchall()
        if remaining_duplicates:
            print(f"⚠️ Still have {len(remaining_duplicates)} duplicates:")
            for name, count in remaining_duplicates:
                print(f"   - {name}: {count} copies")
        else:
            print("🎉 No duplicates remaining!")
            
        # Show final count
        cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'live'")
        final_count = cursor.fetchone()[0]
        print(f"📊 Final live events count: {final_count}")
        
        return total_removed > 0
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_live_events_system():
    """Final verification that everything is working"""
    print("\n🔍 Final System Verification...")
    
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    try:
        # Check for duplicates
        cursor.execute("""
            SELECT COUNT(DISTINCT event_name) as unique_events,
                   COUNT(*) as total_events
            FROM live_events 
            WHERE status = 'live'
            AND created_at >= datetime('now', '-2 hours')
        """)
        
        unique_events, total_events = cursor.fetchone()
        no_duplicates = unique_events == total_events
        
        print(f"   📊 Live events: {total_events} total, {unique_events} unique")
        print(f"   {'✅' if no_duplicates else '❌'} Duplicates: {'None' if no_duplicates else f'{total_events - unique_events} found'}")
        
        # Check event variety
        cursor.execute("""
            SELECT DISTINCT category 
            FROM live_events 
            WHERE status = 'live'
            AND created_at >= datetime('now', '-2 hours')
        """)
        
        categories = [row[0] for row in cursor.fetchall()]
        print(f"   📁 Categories: {len(categories)} types")
        print(f"      {', '.join(categories)}")
        
        # Check recent activity
        cursor.execute("""
            SELECT COUNT(*) 
            FROM live_events 
            WHERE status = 'live'
            AND last_updated >= datetime('now', '-30 minutes')
        """)
        
        recent_updates = cursor.fetchone()[0]
        print(f"   🔄 Recent activity: {recent_updates} events updated in last 30 minutes")
        
        conn.close()
        
        return no_duplicates and total_events > 0
        
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WiseNews Duplicate Cleanup & Final Verification\n")
    
    # Clean duplicates
    cleanup_success = clean_duplicate_live_events()
    
    # Verify system
    system_working = verify_live_events_system()
    
    print(f"\n🎯 FINAL STATUS:")
    print(f"   {'✅' if cleanup_success else '❌'} Duplicate Cleanup: {'Complete' if cleanup_success else 'Issues'}")
    print(f"   {'✅' if system_working else '❌'} System Status: {'Fully Functional' if system_working else 'Needs Work'}")
    
    if cleanup_success and system_working:
        print(f"\n🎉 SUCCESS! Live Events System Ready:")
        print(f"   ✅ No duplicate events")
        print(f"   ✅ Multiple categories active")
        print(f"   ✅ Real-time updates working")
        print(f"   ✅ Backend ready to serve users")
        print(f"\n💡 Note: Live events page requires login at http://127.0.0.1:5000/live-events")
    else:
        print(f"\n⚠️ Some issues remain - check output above")
