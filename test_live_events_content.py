import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta

def test_live_events_page_content():
    """Test the actual content displayed on the live events page"""
    print("🔍 Testing Live Events Page Content...")
    
    try:
        # Get page content
        response = requests.get('http://127.0.0.1:5000/live-events', timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Page not accessible: {response.status_code}")
            return False
            
        print(f"✅ Page accessible (Status: {response.status_code})")
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for live events content
        page_text = soup.get_text().lower()
        
        # Check for key indicators
        indicators = {
            'live events': 'live events' in page_text,
            'bitcoin': 'bitcoin' in page_text,
            'federal reserve': 'federal reserve' in page_text,
            'apple': 'apple' in page_text,
            'sec': 'sec' in page_text,
            'treasury': 'treasury' in page_text,
            'no live events': 'no live events' in page_text or 'no events' in page_text
        }
        
        print(f"\n📊 Content Analysis:")
        for indicator, found in indicators.items():
            status = "✅" if found else "❌"
            print(f"   {status} {indicator.title()}: {'Found' if found else 'Not found'}")
            
        # Look for event cards or lists
        event_elements = soup.find_all(['div', 'li'], class_=lambda x: x and ('event' in x.lower() or 'card' in x.lower()))
        print(f"\n🎯 Event Elements Found: {len(event_elements)}")
        
        # Look for specific live event names from database
        expected_events = [
            'Bitcoin Price Movement',
            'Federal Reserve Policy Decision', 
            'Apple Inc. Quarterly Earnings',
            'SEC Major Enforcement Action',
            'Liverpool vs Manchester United'
        ]
        
        found_events = []
        for event_name in expected_events:
            if event_name.lower() in page_text:
                found_events.append(event_name)
                print(f"   ✅ Found: {event_name}")
            else:
                print(f"   ❌ Missing: {event_name}")
                
        # Check if page shows "no events" when it should show events
        if indicators['no live events'] and len(found_events) == 0:
            print(f"\n⚠️ WARNING: Page shows 'no live events' but database has 16 active events")
            return False
        elif len(found_events) > 0:
            print(f"\n✅ SUCCESS: Page displays {len(found_events)} actual live events")
            return True
        else:
            print(f"\n❌ ISSUE: Page accessible but not showing expected live events")
            
            # Debug: Show some page content
            print(f"\n🔍 Page Content Sample (first 500 chars):")
            print(f"   {response.text[:500]}...")
            
            return False
            
    except Exception as e:
        print(f"❌ Error testing page content: {e}")
        return False

def compare_backend_vs_frontend():
    """Compare what's in the database vs what's shown on the page"""
    print(f"\n🔄 Comparing Backend vs Frontend...")
    
    try:
        # Get backend data
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        two_hours_ago = datetime.now() - timedelta(hours=2)
        cursor.execute("""
            SELECT event_name, category FROM live_events 
            WHERE status = 'live' 
            AND last_updated >= ?
            ORDER BY last_updated DESC
        """, (two_hours_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        
        backend_events = cursor.fetchall()
        conn.close()
        
        print(f"📊 Backend Events ({len(backend_events)}):")
        for name, category in backend_events:
            print(f"   📍 {name} ({category})")
            
        # Get frontend data
        response = requests.get('http://127.0.0.1:5000/live-events')
        page_text = response.text.lower()
        
        print(f"\n🌐 Frontend Check:")
        matches = 0
        for name, category in backend_events:
            if name.lower() in page_text:
                print(f"   ✅ {name} - Displayed")
                matches += 1
            else:
                print(f"   ❌ {name} - Not displayed")
                
        print(f"\n📈 Match Rate: {matches}/{len(backend_events)} ({int(matches/len(backend_events)*100) if backend_events else 0}%)")
        
        return matches > 0
        
    except Exception as e:
        print(f"❌ Error comparing data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 WiseNews Live Events Content Verification\n")
    
    # Test page content
    content_working = test_live_events_page_content()
    
    # Compare backend vs frontend
    frontend_working = compare_backend_vs_frontend()
    
    print(f"\n🎯 Final Assessment:")
    print(f"   {'✅' if content_working else '❌'} Page Content: {'Working' if content_working else 'Issues detected'}")
    print(f"   {'✅' if frontend_working else '❌'} Backend/Frontend Sync: {'Working' if frontend_working else 'Not synced'}")
    
    if content_working and frontend_working:
        print(f"\n🎉 SUCCESS: Live events are properly displaying actual events!")
    else:
        print(f"\n⚠️ ATTENTION NEEDED: Live events page needs further investigation")
