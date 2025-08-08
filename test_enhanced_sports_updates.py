#!/usr/bin/env python3
"""
Test Enhanced Sports Updates
============================
Create test sports events and generate enhanced notifications to verify the improvements.
"""

import sqlite3
import json
from datetime import datetime

def test_enhanced_sports_updates():
    """Test the enhanced sports update system"""
    
    print("🏆 TESTING ENHANCED SPORTS UPDATES")
    print("=" * 50)
    
    try:
        # Initialize live events manager
        from live_events_manager import live_events_manager
        
        # Create a test football match
        test_match = {
            'name': 'Manchester City vs Arsenal',
            'type': 'sports',
            'category': 'football',
            'status': 'live',
            'start_time': datetime.now().isoformat(),
            'venue': 'Etihad Stadium',
            'description': 'Premier League Championship Match',
            'external_id': 'test_enhanced_match_001',
            'data_source': 'test_enhanced_api',
            'metadata': {
                'home_team': 'Manchester City',
                'away_team': 'Arsenal',
                'score': {'home': 1, 'away': 1},
                'minute': 75
            }
        }
        
        print("📝 Creating test match...")
        event_id = live_events_manager.create_event(test_match)
        
        if event_id:
            print(f"✅ Created test match with ID: {event_id}")
            
            # Generate various types of enhanced sports updates
            test_updates = [
                {
                    'type': 'goal',
                    'title': 'Test Goal Update',
                    'content': 'Test goal content',
                    'importance': 0.9,
                    'metadata': {
                        'minute': 78,
                        'scorer': 'De Bruyne',
                        'assist': 'Haaland',
                        'score': {'home': 2, 'away': 1},
                        'goal_type': 'left foot',
                        'update_type': 'goal'
                    }
                },
                {
                    'type': 'card',
                    'title': 'Test Yellow Card',
                    'content': 'Test card content',
                    'importance': 0.3,
                    'metadata': {
                        'minute': 82,
                        'player': 'Xhaka',
                        'card_type': 'yellow',
                        'reason': 'unsporting behavior',
                        'update_type': 'card'
                    }
                },
                {
                    'type': 'substitution',
                    'title': 'Test Substitution',
                    'content': 'Test substitution content',
                    'importance': 0.4,
                    'metadata': {
                        'minute': 85,
                        'player_on': 'Foden',
                        'player_off': 'Grealish',
                        'update_type': 'substitution'
                    }
                },
                {
                    'type': 'penalty',
                    'title': 'Test Penalty',
                    'content': 'Test penalty content',
                    'importance': 0.7,
                    'metadata': {
                        'minute': 88,
                        'awarded_to': 'Arsenal',
                        'update_type': 'penalty'
                    }
                },
                {
                    'type': 'near_miss',
                    'title': 'Test Near Miss',
                    'content': 'Test near miss content',
                    'importance': 0.5,
                    'metadata': {
                        'minute': 90,
                        'player': 'Saka',
                        'outcome': 'crossbar',
                        'update_type': 'near_miss'
                    }
                }
            ]
            
            print("\n📊 Generating enhanced sports updates...")
            for i, update in enumerate(test_updates, 1):
                success = live_events_manager.add_event_update(event_id, update)
                if success:
                    print(f"   ✅ Update {i}: {update['metadata']['update_type']} - {update['metadata'].get('minute', '?')}'")
                else:
                    print(f"   ❌ Failed to add update {i}")
            
            # Check the notifications that were created
            print("\n📋 Checking generated notifications...")
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get recent notifications from the last minute
            cursor.execute('''
                SELECT title, content, category, notification_type, date_added
                FROM notifications 
                WHERE date_added > datetime('now', '-1 minute')
                AND (title LIKE '%De Bruyne%' OR title LIKE '%Xhaka%' OR title LIKE '%Foden%' OR title LIKE '%Arsenal%')
                ORDER BY date_added DESC
                LIMIT 10
            ''')
            
            new_notifications = cursor.fetchall()
            
            if new_notifications:
                print(f"   🎯 Found {len(new_notifications)} new enhanced notifications:")
                for i, notif in enumerate(new_notifications, 1):
                    title = notif[0]
                    content = notif[1][:80] + "..." if len(notif[1]) > 80 else notif[1]
                    print(f"\n   {i}. TITLE: {title}")
                    print(f"      CONTENT: {content}")
                    print(f"      CATEGORY: {notif[2]}")
            else:
                print("   ⚠️ No enhanced notifications found - checking live event updates...")
                
                # Check live event updates instead
                cursor.execute('''
                    SELECT title, content, update_type, metadata
                    FROM live_event_updates 
                    WHERE event_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (event_id,))
                
                updates = cursor.fetchall()
                
                if updates:
                    print(f"   📊 Found {len(updates)} live event updates:")
                    for i, update in enumerate(updates, 1):
                        title = update[0]
                        content = update[1][:80] + "..." if len(update[1]) > 80 else update[1]
                        update_type = update[2]
                        print(f"\n   {i}. [{update_type.upper()}] {title}")
                        print(f"      {content}")
            
            conn.close()
            
        else:
            print("❌ Failed to create test match")
            
    except Exception as e:
        print(f"❌ Error testing enhanced sports updates: {e}")
        import traceback
        traceback.print_exc()

def check_sports_update_improvements():
    """Check the improvements in sports update format"""
    
    print("\n🔍 CHECKING SPORTS UPDATE IMPROVEMENTS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get recent sports-related notifications
        cursor.execute('''
            SELECT title, content, category, date_added
            FROM notifications 
            WHERE (category LIKE '%sport%' OR category LIKE '%football%' OR category LIKE '%basketball%' 
                   OR title LIKE '%GOAL%' OR title LIKE '%Card%' OR title LIKE '%SUB%')
            ORDER BY date_added DESC
            LIMIT 15
        ''')
        
        sports_notifications = cursor.fetchall()
        
        print(f"📊 Recent sports notifications: {len(sports_notifications)}")
        
        if sports_notifications:
            print("\n📋 SPORTS NOTIFICATION ANALYSIS:")
            
            enhanced_count = 0
            for i, notif in enumerate(sports_notifications, 1):
                title = notif[0]
                content = notif[1]
                
                # Check if it uses enhanced format
                is_enhanced = any(indicator in title for indicator in ['⚽', '🟨', '🟥', '🔄', '🎯', '💥', '🏀'])
                has_priority = any(priority in title for priority in ['🚨 MAJOR', '📝 UPDATE', 'ℹ️ INFO'])
                
                if is_enhanced:
                    enhanced_count += 1
                
                status = "✅ ENHANCED" if is_enhanced else "⚠️ OLD FORMAT"
                priority_status = " + PRIORITY" if has_priority else ""
                
                print(f"\n   {i}. {status}{priority_status}")
                print(f"      TITLE: {title[:100]}")
                print(f"      CONTENT: {content[:100]}...")
        
            enhancement_rate = (enhanced_count / len(sports_notifications)) * 100
            print(f"\n📈 ENHANCEMENT RATE: {enhancement_rate:.1f}% ({enhanced_count}/{len(sports_notifications)})")
            
            if enhancement_rate > 50:
                print("✅ Sports updates are being enhanced successfully!")
            else:
                print("⚠️ More sports updates need enhancement")
        
        else:
            print("   ⚠️ No recent sports notifications found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking improvements: {e}")

def main():
    """Main testing function"""
    print("🧪 ENHANCED SPORTS UPDATES TEST SUITE")
    print("=" * 60)
    
    # Test the enhanced sports update system
    test_enhanced_sports_updates()
    
    # Check improvements
    check_sports_update_improvements()
    
    print("\n🎯 TESTING COMPLETE!")
    print("Enhanced sports updates should now show:")
    print("✅ Specific details (scorer, minute, score)")
    print("✅ Clear action indicators (⚽, 🟨, 🟥, 🔄)")
    print("✅ Priority levels (🚨 MAJOR, 📝 UPDATE)")
    print("✅ Concise, relevant information")
    print("✅ Perfect format for Quick Updates")

if __name__ == "__main__":
    main()
