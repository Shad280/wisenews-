"""
Test Live Events Creator
Creates sample live events for testing the archiving system
"""

import sqlite3
import datetime
import json

def create_test_live_events():
    """Create test live events with different sizes and statuses"""
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    # Get current time
    now = datetime.datetime.now()
    
    # Create test events
    test_events = [
        {
            'event_name': 'NBA Finals Game 7 - Lakers vs Celtics',
            'event_type': 'sports',
            'category': 'basketball',
            'status': 'completed',
            'start_time': (now - datetime.timedelta(hours=3)).isoformat(),
            'end_time': (now - datetime.timedelta(hours=1)).isoformat(),
            'venue': 'Crypto.com Arena',
            'description': 'The decisive Game 7 of the NBA Finals between the Los Angeles Lakers and Boston Celtics. A historic matchup between two of the most successful franchises in NBA history.',
            'external_id': 'nba_finals_2025_g7',
            'data_source': 'NBA_API',
            'metadata': json.dumps({'attendance': 20000, 'tv_viewers': '50M'})
        },
        {
            'event_name': 'Stock Market Close - Record High',
            'event_type': 'finance',
            'category': 'stocks',
            'status': 'completed',
            'start_time': (now - datetime.timedelta(hours=1)).isoformat(),
            'end_time': now.isoformat(),
            'venue': 'NYSE',
            'description': 'Market closes at record high',
            'external_id': 'nyse_close_080625',
            'data_source': 'MARKET_API',
            'metadata': json.dumps({'dow_close': 45500, 'sp500_close': 5800})
        },
        {
            'event_name': 'Presidential Press Conference',
            'event_type': 'conference',
            'category': 'politics',
            'status': 'completed',
            'start_time': (now - datetime.timedelta(hours=2)).isoformat(),
            'end_time': (now - datetime.timedelta(hours=1, minutes=30)).isoformat(),
            'venue': 'White House',
            'description': 'President addresses the nation on economic policy, infrastructure investments, and foreign relations. The comprehensive briefing covered multiple policy areas.',
            'external_id': 'potus_presser_080625',
            'data_source': 'GOV_API',
            'metadata': json.dumps({'duration_minutes': 30, 'questions_taken': 12})
        }
    ]
    
    # Insert events
    for event in test_events:
        cursor.execute('''
            INSERT INTO live_events (
                event_name, event_type, category, status, start_time, end_time,
                venue, description, external_id, data_source, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['event_name'], event['event_type'], event['category'],
            event['status'], event['start_time'], event['end_time'],
            event['venue'], event['description'], event['external_id'],
            event['data_source'], event['metadata']
        ))
        
        event_id = cursor.lastrowid
        
        # Add some updates for each event
        if event['event_type'] == 'sports':
            updates = [
                ('Game Started', 'Tip-off at Crypto.com Arena', 'announcement'),
                ('First Quarter Score', 'Lakers 28 - Celtics 24', 'score'),
                ('Halftime Score', 'Lakers 58 - Celtics 55', 'score'),
                ('Third Quarter Score', 'Lakers 82 - Celtics 81', 'score'),
                ('Final Score', 'Lakers 112 - Celtics 108. Lakers win the NBA Championship!', 'score'),
                ('Championship Celebration', 'Lakers players celebrate with confetti falling. LeBron James named Finals MVP.', 'announcement')
            ]
        elif event['event_type'] == 'finance':
            updates = [
                ('Market Update', 'DOW up 1.2% at midday', 'price_change'),
                ('Final Numbers', 'DOW closes at 45,500 (+2.1%), S&P 500 at 5,800 (+1.8%)', 'price_change')
            ]
        else:  # conference
            updates = [
                ('Press Conference Begins', 'President takes the podium', 'announcement'),
                ('Economic Policy', 'Announces new infrastructure bill worth $2 trillion', 'quote'),
                ('Foreign Relations', 'Discusses strengthening NATO alliances', 'quote'),
                ('Q&A Session', 'Taking questions from press corps', 'announcement'),
                ('Conference Ends', 'President concludes after 30 minutes', 'announcement')
            ]
        
        # Insert updates
        for i, (title, content, update_type) in enumerate(updates):
            update_time = datetime.datetime.fromisoformat(event['start_time']) + datetime.timedelta(minutes=i*10)
            importance = 0.9 if 'Final' in title or 'Championship' in title else 0.5
            
            cursor.execute('''
                INSERT INTO live_event_updates (
                    event_id, update_type, title, content, timestamp, importance
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_id, update_type, title, content, update_time.isoformat(), importance))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {len(test_events)} test live events with updates")
    return len(test_events)

if __name__ == '__main__':
    create_test_live_events()
