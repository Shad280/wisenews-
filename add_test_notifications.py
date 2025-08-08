import sqlite3
import datetime

conn = sqlite3.connect('news_database.db')
cursor = conn.cursor()

# Add some sample notifications
notifications = [
    ('Stock Market Update', 'DOW Jones up 2.3% in early trading', 'Financial', 'Bloomberg', datetime.datetime.now().isoformat(), 'high', 'market_update'),
    ('Breaking: Tech Merger', 'Major software companies announce merger talks', 'Technology', 'TechCrunch', datetime.datetime.now().isoformat(), 'high', 'breaking_news'),
    ('Weather Alert', 'Heavy rain expected in northeastern regions', 'Weather', 'Weather Channel', datetime.datetime.now().isoformat(), 'medium', 'weather_alert'),
    ('Sports Update', 'Championship game delayed due to weather', 'Sports', 'ESPN', datetime.datetime.now().isoformat(), 'low', 'sports_update'),
    ('Economic Brief', 'Unemployment rate drops to 3.8%', 'Economics', 'Reuters', datetime.datetime.now().isoformat(), 'medium', 'economic_report')
]

for title, content, category, source, date_added, priority, notification_type in notifications:
    cursor.execute('''
        INSERT INTO notifications (title, content, category, source_name, date_added, priority, notification_type, is_read)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    ''', (title, content, category, source, date_added, priority, notification_type))

conn.commit()
conn.close()
print('✅ Sample notifications added successfully!')
