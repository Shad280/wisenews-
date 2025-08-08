#!/usr/bin/env python3
"""
Quick test script to check article database access
"""

import sqlite3
import json
from datetime import datetime

def test_article_access():
    """Test if we can access articles from the database"""
    try:
        # Connect to database
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get article count
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_deleted = 0 OR is_deleted IS NULL")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total active articles in database: {total_count}")
        
        # Get recent articles
        cursor.execute("""
            SELECT id, title, source_name, date_added, category, read_status 
            FROM articles 
            WHERE is_deleted = 0 OR is_deleted IS NULL 
            ORDER BY date_added DESC 
            LIMIT 10
        """)
        recent_articles = cursor.fetchall()
        
        print(f"\n📰 Recent articles:")
        for article in recent_articles:
            article_id, title, source, date_added, category, read_status = article
            status = "✅ Read" if read_status else "📖 Unread"
            print(f"  {article_id}: {title[:60]}...")
            print(f"      Source: {source} | Category: {category} | {status}")
            print(f"      Date: {date_added}")
            print()
        
        # Test filtering by category
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM articles 
            WHERE is_deleted = 0 OR is_deleted IS NULL 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        """)
        categories = cursor.fetchall()
        
        print(f"📂 Articles by category:")
        for category, count in categories:
            print(f"  {category or 'Uncategorized'}: {count} articles")
        
        # Test search functionality
        cursor.execute("""
            SELECT id, title 
            FROM articles 
            WHERE (is_deleted = 0 OR is_deleted IS NULL) 
            AND (title LIKE '%Trump%' OR content LIKE '%Trump%')
            LIMIT 5
        """)
        search_results = cursor.fetchall()
        
        print(f"\n🔍 Sample search results for 'Trump':")
        for article_id, title in search_results:
            print(f"  {article_id}: {title}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error accessing articles: {e}")
        return False

def test_web_access():
    """Test accessing articles through web interface"""
    try:
        import requests
        
        # Test dashboard access
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200:
            print(f"✅ Dashboard accessible: HTTP {response.status_code}")
        else:
            print(f"❌ Dashboard access failed: HTTP {response.status_code}")
            
        # Test articles API endpoint
        response = requests.get('http://localhost:5000/articles', timeout=10)
        if response.status_code == 200:
            print(f"✅ Articles page accessible: HTTP {response.status_code}")
        else:
            print(f"❌ Articles page access failed: HTTP {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing web access: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing WiseNews Article Access...")
    print("=" * 50)
    
    # Test database access
    print("\n1. Testing Database Access:")
    db_success = test_article_access()
    
    # Test web access
    print("\n2. Testing Web Interface Access:")
    web_success = test_web_access()
    
    print(f"\n{'✅ Article access is working!' if db_success else '❌ Article access has issues!'}")
