#!/usr/bin/env python3
import sqlite3

def check_live_events_tables():
    """Check for live events related tables in the database"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [table[0] for table in cursor.fetchall()]
        
        # Filter for live/event related tables
        live_event_tables = [table for table in all_tables if 'live' in table.lower() or 'event' in table.lower()]
        
        print("Live/Event related tables:")
        for table in live_event_tables:
            print(f"  - {table}")
        
        # Check articles table for live_event source_type
        cursor.execute("SELECT DISTINCT source_type FROM articles WHERE source_type LIKE '%live%' OR source_type LIKE '%event%'")
        live_sources = cursor.fetchall()
        
        print("\nLive/Event source types in articles:")
        for source in live_sources:
            print(f"  - {source[0]}")
            
        # Count live event articles
        cursor.execute("SELECT COUNT(*) FROM articles WHERE source_type = 'live_event'")
        live_count = cursor.fetchone()[0]
        print(f"\nTotal live_event articles: {live_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_live_events_tables()
