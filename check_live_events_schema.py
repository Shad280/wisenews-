#!/usr/bin/env python3
import sqlite3

def check_live_events_schema():
    """Check the schema and sample data for live events"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get live_events table schema
        cursor.execute("PRAGMA table_info(live_events)")
        columns = cursor.fetchall()
        
        print("live_events table schema:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
        
        # Get sample data showing event status
        print("\nSample live events data:")
        cursor.execute("SELECT id, event_name, status, start_time, end_time FROM live_events ORDER BY id DESC LIMIT 10")
        events = cursor.fetchall()
        
        for event in events:
            print(f"  ID: {event[0]}, Name: {event[1]}, Status: {event[2]}, Start: {event[3]}, End: {event[4]}")
        
        # Check status distribution
        print("\nEvent status distribution:")
        cursor.execute("SELECT status, COUNT(*) FROM live_events GROUP BY status")
        status_counts = cursor.fetchall()
        
        for status, count in status_counts:
            print(f"  {status}: {count} events")
            
        # Check if there are any ongoing live events
        cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'live'")
        live_count = cursor.fetchone()[0]
        print(f"\nCurrently live events: {live_count}")
        
        # Check how live events appear in articles
        print("\nLive events in articles table:")
        cursor.execute("SELECT id, title, source_type, source_name FROM articles WHERE source_type = 'live_event' ORDER BY date_added DESC LIMIT 5")
        articles = cursor.fetchall()
        
        for article in articles:
            print(f"  Article ID: {article[0]}, Title: {article[1]}, Source: {article[2]}, Source Name: {article[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_live_events_schema()
