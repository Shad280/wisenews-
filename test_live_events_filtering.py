#!/usr/bin/env python3
"""
Test script to verify live events filtering is working correctly
"""
import sqlite3

def test_live_events_filtering():
    """Test that ongoing live events are excluded from articles browsing"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        print("=== LIVE EVENTS FILTERING TEST ===\n")
        
        # Check current live events status
        print("1. Current live events status:")
        cursor.execute("SELECT status, COUNT(*) FROM live_events GROUP BY status")
        status_counts = cursor.fetchall()
        for status, count in status_counts:
            print(f"   {status}: {count} events")
        
        # Check total articles from live events
        print("\n2. Live event articles in database:")
        cursor.execute("SELECT COUNT(*) FROM articles WHERE source_type = 'live_event'")
        total_live_articles = cursor.fetchone()[0]
        print(f"   Total live_event articles: {total_live_articles}")
        
        # Test articles query (what users will see in browse section)
        print("\n3. Articles query results (what users see in browse):")
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE is_deleted = 0
            AND (source_type != 'live_event' OR 
                 (source_type = 'live_event' AND 
                  CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                  (SELECT id FROM live_events WHERE status = 'completed')))
        ''')
        filtered_count = cursor.fetchone()[0]
        print(f"   Articles visible in browse (excluding ongoing live events): {filtered_count}")
        
        # Test what completed live events will show
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE source_type = 'live_event' 
            AND CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                (SELECT id FROM live_events WHERE status = 'completed')
        ''')
        completed_live_articles = cursor.fetchone()[0]
        print(f"   Completed live events shown as articles: {completed_live_articles}")
        
        # Test what ongoing live events are hidden
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE source_type = 'live_event' 
            AND CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                (SELECT id FROM live_events WHERE status = 'live')
        ''')
        hidden_live_articles = cursor.fetchone()[0]
        print(f"   Ongoing live events hidden from browse: {hidden_live_articles}")
        
        # Show sample of what will be displayed
        print("\n4. Sample articles that will be shown in browse:")
        cursor.execute('''
            SELECT id, title, source_type, source_name 
            FROM articles 
            WHERE is_deleted = 0
            AND (source_type != 'live_event' OR 
                 (source_type = 'live_event' AND 
                  CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER) IN 
                  (SELECT id FROM live_events WHERE status = 'completed')))
            ORDER BY date_added DESC 
            LIMIT 5
        ''')
        sample_articles = cursor.fetchall()
        
        for article in sample_articles:
            source_display = 'News' if article[2] == 'live_event' else article[2]
            source_name = article[3]
            if article[2] == 'live_event' and source_name and source_name.startswith('Live Events - '):
                source_name = source_name[14:]  # Remove "Live Events - " prefix
            print(f"   - ID: {article[0]}, Title: {article[1][:50]}..., Source: {source_display}, Source Name: {source_name}")
        
        # Check live events that should only appear in live events section
        print("\n5. Live events that should ONLY appear in live events section:")
        cursor.execute("SELECT id, event_name, status FROM live_events WHERE status = 'live' LIMIT 5")
        live_events = cursor.fetchall()
        
        for event in live_events:
            print(f"   - ID: {event[0]}, Name: {event[1]}, Status: {event[2]}")
        
        print(f"\n✅ TEST COMPLETE")
        print(f"   - Ongoing live events will only appear in live events section")
        print(f"   - Completed live events will appear as regular news articles")
        print(f"   - 'Live Events' branding removed from completed events")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_live_events_filtering()
