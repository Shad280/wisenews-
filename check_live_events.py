#!/usr/bin/env python3
"""Check live events database for duplicates and issues."""

import sqlite3
from datetime import datetime, timedelta

def check_live_events():
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()

    # Check live events
    print('=== LIVE EVENTS ===')
    cursor.execute('SELECT id, event_name, category, status, start_time, last_updated FROM live_events ORDER BY id DESC LIMIT 20')
    events = cursor.fetchall()
    for event in events:
        print(f'ID: {event[0]}, Name: {event[1][:50]}, Category: {event[2]}, Status: {event[3]}, Start: {event[4]}, Updated: {event[5]}')

    print('\n=== EVENT UPDATES COUNT ===')
    cursor.execute('SELECT event_id, COUNT(*) as update_count FROM live_event_updates GROUP BY event_id ORDER BY update_count DESC LIMIT 10')
    updates = cursor.fetchall()
    for update in updates:
        print(f'Event ID: {update[0]}, Updates: {update[1]}')

    print('\n=== RECENT EVENTS (last 5 minutes) ===')
    cursor.execute("SELECT COUNT(*) FROM live_events WHERE start_time >= datetime('now', '-5 minutes')")
    recent_count = cursor.fetchone()[0]
    print(f'Events created in last 5 minutes: {recent_count}')

    print('\n=== DUPLICATE EVENT NAMES ===')
    cursor.execute('SELECT event_name, COUNT(*) as count FROM live_events GROUP BY event_name HAVING count > 1 ORDER BY count DESC LIMIT 10')
    duplicates = cursor.fetchall()
    for dup in duplicates:
        print(f'Event: {dup[0][:50]}, Count: {dup[1]}')

    print('\n=== ACTIVE EVENTS ===')
    cursor.execute("SELECT COUNT(*) FROM live_events WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    print(f'Active events: {active_count}')

    print('\n=== OLD EVENTS (older than 5 minutes) ===')
    cursor.execute("SELECT COUNT(*) FROM live_events WHERE start_time < datetime('now', '-5 minutes') AND status = 'active'")
    old_active_count = cursor.fetchone()[0]
    print(f'Old active events (>5 min): {old_active_count}')

    conn.close()

if __name__ == "__main__":
    check_live_events()
