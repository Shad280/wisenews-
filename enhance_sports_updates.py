#!/usr/bin/env python3
"""
Enhanced Sports Updates for Quick Updates
========================================
Improve sports notifications to show specific details like goals, scores, assists, 
and remove unnecessary information while maintaining clarity and excitement.
"""

import sqlite3
import json
from datetime import datetime
import re

def enhance_sports_update_generation():
    """Update the live events manager to generate better sports updates"""
    
    print("🏆 ENHANCING SPORTS UPDATES FOR QUICK UPDATES")
    print("=" * 60)
    
    # First, let's check current sports notifications
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get current sports notifications
        cursor.execute('''
            SELECT id, title, content, category, date_added, notification_type
            FROM notifications 
            WHERE category IN ('Sports', 'sports', 'football', 'basketball', 'tennis', 'baseball', 'soccer')
            ORDER BY date_added DESC
            LIMIT 10
        ''')
        
        sports_notifications = cursor.fetchall()
        
        print(f"📊 Current sports notifications: {len(sports_notifications)}")
        
        if sports_notifications:
            print("\n📋 CURRENT SPORTS NOTIFICATIONS:")
            for i, notif in enumerate(sports_notifications, 1):
                title = notif[1][:80] if notif[1] else 'No title'
                content_preview = notif[2][:100] if notif[2] else 'No content'
                print(f"   {i}. {title}")
                print(f"      Content: {content_preview}...")
                print()
        
        # Check live event updates for sports
        cursor.execute('''
            SELECT leu.id, leu.title, leu.content, leu.update_type, leu.metadata, le.category
            FROM live_event_updates leu
            JOIN live_events le ON leu.event_id = le.id
            WHERE le.category IN ('football', 'basketball', 'tennis', 'baseball', 'soccer')
            ORDER BY leu.timestamp DESC
            LIMIT 10
        ''')
        
        sports_updates = cursor.fetchall()
        
        print(f"⚽ Live sports updates: {len(sports_updates)}")
        
        if sports_updates:
            print("\n📋 CURRENT LIVE SPORTS UPDATES:")
            for i, update in enumerate(sports_updates, 1):
                title = update[1][:80] if update[1] else 'No title'
                update_type = update[3] or 'unknown'
                category = update[5] or 'sports'
                print(f"   {i}. [{category.upper()}] {update_type}: {title}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking current sports updates: {e}")

def create_enhanced_sports_update_functions():
    """Create enhanced sports update generation functions"""
    
    enhanced_functions = """
def _generate_enhanced_sports_update(self, event_id: int, event_data: Dict):
    '''Generate enhanced sports updates with specific details'''
    import random
    
    if random.random() < 0.15:  # 15% chance of update
        current_score = event_data['metadata']['score']
        minute = event_data['metadata']['minute']
        home_team = event_data['metadata']['home_team']
        away_team = event_data['metadata']['away_team']
        
        # Enhanced update types with specific details
        updates = [
            {
                'type': 'goal',
                'title': f"GOAL! {home_team} {current_score['home'] + 1}-{current_score['away']} {away_team}",
                'content': f"⚽ GOAL: {home_team} scores in the {minute}' - {self._get_goal_scorer()} finds the net! Score: {current_score['home'] + 1}-{current_score['away']}",
                'importance': 0.9,
                'metadata': {
                    'minute': minute,
                    'scorer': self._get_goal_scorer(),
                    'assist': self._get_assist_player(),
                    'score': {'home': current_score['home'] + 1, 'away': current_score['away']},
                    'goal_type': random.choice(['header', 'left foot', 'right foot', 'penalty', 'free kick']),
                    'update_type': 'goal'
                }
            },
            {
                'type': 'goal',
                'title': f"GOAL! {home_team} {current_score['home']}-{current_score['away'] + 1} {away_team}",
                'content': f"⚽ GOAL: {away_team} scores in the {minute}' - {self._get_goal_scorer()} converts! Score: {current_score['home']}-{current_score['away'] + 1}",
                'importance': 0.9,
                'metadata': {
                    'minute': minute,
                    'scorer': self._get_goal_scorer(),
                    'assist': self._get_assist_player(),
                    'score': {'home': current_score['home'], 'away': current_score['away'] + 1},
                    'goal_type': random.choice(['header', 'left foot', 'right foot', 'penalty', 'free kick']),
                    'update_type': 'goal'
                }
            },
            {
                'type': 'card',
                'title': f"Yellow Card - {random.choice([home_team, away_team])}",
                'content': f"🟨 Yellow Card: {self._get_player_name()} booked for {random.choice(['foul', 'unsporting behavior', 'dissent'])} in the {minute}'",
                'importance': 0.3,
                'metadata': {
                    'minute': minute,
                    'player': self._get_player_name(),
                    'card_type': 'yellow',
                    'reason': random.choice(['foul', 'unsporting behavior', 'dissent']),
                    'update_type': 'card'
                }
            },
            {
                'type': 'red_card',
                'title': f"RED CARD! {random.choice([home_team, away_team])} down to 10 men",
                'content': f"🟥 RED CARD: {self._get_player_name()} sent off in the {minute}' for serious foul play!",
                'importance': 0.8,
                'metadata': {
                    'minute': minute,
                    'player': self._get_player_name(),
                    'card_type': 'red',
                    'reason': 'serious foul play',
                    'update_type': 'red_card'
                }
            },
            {
                'type': 'substitution',
                'title': f"Substitution - {random.choice([home_team, away_team])}",
                'content': f"🔄 SUB: {self._get_player_name()} comes on for {self._get_player_name()} in the {minute}'",
                'importance': 0.4,
                'metadata': {
                    'minute': minute,
                    'player_on': self._get_player_name(),
                    'player_off': self._get_player_name(),
                    'update_type': 'substitution'
                }
            },
            {
                'type': 'penalty',
                'title': f"PENALTY! {random.choice([home_team, away_team])} awarded spot kick",
                'content': f"🎯 PENALTY: {random.choice([home_team, away_team])} awarded penalty in the {minute}' - foul in the box!",
                'importance': 0.7,
                'metadata': {
                    'minute': minute,
                    'awarded_to': random.choice([home_team, away_team]),
                    'update_type': 'penalty'
                }
            },
            {
                'type': 'near_miss',
                'title': f"Close Call! {random.choice([home_team, away_team])} nearly scores",
                'content': f"💥 CLOSE: {self._get_player_name()} hits the {random.choice(['post', 'crossbar', 'side netting'])} in the {minute}'!",
                'importance': 0.5,
                'metadata': {
                    'minute': minute,
                    'player': self._get_player_name(),
                    'outcome': random.choice(['post', 'crossbar', 'side netting']),
                    'update_type': 'near_miss'
                }
            }
        ]
        
        update = random.choice(updates)
        self.add_event_update(event_id, update)

def _get_goal_scorer(self):
    '''Get random player name for goal scorer'''
    scorers = [
        'Johnson', 'Smith', 'Rodriguez', 'Williams', 'Brown', 'Davis', 'Miller', 
        'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 
        'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson'
    ]
    return random.choice(scorers)

def _get_assist_player(self):
    '''Get random player name for assist'''
    return self._get_goal_scorer()  # Use same pool

def _get_player_name(self):
    '''Get random player name'''
    return self._get_goal_scorer()  # Use same pool

def _create_enhanced_sports_notification_title(self, event_name: str, update_data: Dict, event_metadata: Dict) -> str:
    '''Create enhanced sports notification titles'''
    update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type', 'update'))
    
    if update_type == 'goal':
        score = update_data.get('metadata', {}).get('score', {})
        scorer = update_data.get('metadata', {}).get('scorer', 'Player')
        return f"⚽ GOAL: {scorer} scores! {score.get('home', 0)}-{score.get('away', 0)}"
    
    elif update_type == 'card':
        player = update_data.get('metadata', {}).get('player', 'Player')
        card_type = update_data.get('metadata', {}).get('card_type', 'yellow')
        minute = update_data.get('metadata', {}).get('minute', '?')
        emoji = '🟨' if card_type == 'yellow' else '🟥'
        return f"{emoji} {card_type.title()} Card: {player} ({minute}')"
    
    elif update_type == 'red_card':
        player = update_data.get('metadata', {}).get('player', 'Player')
        minute = update_data.get('metadata', {}).get('minute', '?')
        return f"🟥 RED CARD: {player} sent off ({minute}')"
    
    elif update_type == 'substitution':
        player_on = update_data.get('metadata', {}).get('player_on', 'Player')
        minute = update_data.get('metadata', {}).get('minute', '?')
        return f"🔄 SUB: {player_on} comes on ({minute}')"
    
    elif update_type == 'penalty':
        awarded_to = update_data.get('metadata', {}).get('awarded_to', 'Team')
        minute = update_data.get('metadata', {}).get('minute', '?')
        return f"🎯 PENALTY: {awarded_to} awarded ({minute}')"
    
    elif update_type == 'near_miss':
        player = update_data.get('metadata', {}).get('player', 'Player')
        outcome = update_data.get('metadata', {}).get('outcome', 'post')
        minute = update_data.get('metadata', {}).get('minute', '?')
        return f"💥 CLOSE: {player} hits {outcome} ({minute}')"
    
    else:
        return f"🏆 {event_name} - {update_type.replace('_', ' ').title()}"

def _create_enhanced_sports_notification_content(self, update_data: Dict, event_metadata: Dict) -> str:
    '''Create enhanced sports notification content with minimal, relevant details'''
    update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type', 'update'))
    minute = update_data.get('metadata', {}).get('minute', '?')
    
    if update_type == 'goal':
        scorer = update_data.get('metadata', {}).get('scorer', 'Player')
        assist = update_data.get('metadata', {}).get('assist', '')
        goal_type = update_data.get('metadata', {}).get('goal_type', 'shot')
        score = update_data.get('metadata', {}).get('score', {})
        
        content = f"⚽ {scorer} scores with {goal_type} in the {minute}'"
        if assist:
            content += f" (assist: {assist})"
        content += f" • Score: {score.get('home', 0)}-{score.get('away', 0)}"
        return content
    
    elif update_type in ['card', 'red_card']:
        player = update_data.get('metadata', {}).get('player', 'Player')
        reason = update_data.get('metadata', {}).get('reason', 'foul')
        card_type = update_data.get('metadata', {}).get('card_type', 'yellow')
        emoji = '🟨' if card_type == 'yellow' else '🟥'
        return f"{emoji} {player} booked for {reason} ({minute}')"
    
    elif update_type == 'substitution':
        player_on = update_data.get('metadata', {}).get('player_on', 'Player A')
        player_off = update_data.get('metadata', {}).get('player_off', 'Player B')
        return f"🔄 {player_on} replaces {player_off} ({minute}')"
    
    elif update_type == 'penalty':
        awarded_to = update_data.get('metadata', {}).get('awarded_to', 'Team')
        return f"🎯 Penalty awarded to {awarded_to} for foul in box ({minute}')"
    
    elif update_type == 'near_miss':
        player = update_data.get('metadata', {}).get('player', 'Player')
        outcome = update_data.get('metadata', {}).get('outcome', 'post')
        return f"💥 {player} strikes the {outcome} - so close! ({minute}')"
    
    else:
        return update_data.get('content', f"Live update from {minute}'")
"""
    
    print("\n📝 ENHANCED SPORTS UPDATE FUNCTIONS:")
    print("✅ Enhanced goal notifications with scorer, assist, and score")
    print("✅ Simplified card notifications with player and reason")
    print("✅ Clear substitution updates with player names")
    print("✅ Penalty and near-miss notifications")
    print("✅ Removed unnecessary verbose content")
    print("✅ Added specific emojis for quick recognition")
    
    return enhanced_functions

def update_sports_notification_creation():
    """Update how sports notifications are created to be more concise and informative"""
    
    print("\n🔧 UPDATING SPORTS NOTIFICATION CREATION...")
    
    enhanced_notification_code = '''
# Enhanced sports notification creation in _trigger_event_notifications
if category in ['football', 'basketball', 'tennis', 'baseball', 'soccer']:
    # Create enhanced sports notification
    notification_title = self._create_enhanced_sports_notification_title(
        event_name, update_data, event_metadata
    )
    
    notification_content = self._create_enhanced_sports_notification_content(
        update_data, event_metadata
    )
    
    # Add context only if it's a major event (goal, red card, penalty)
    update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type'))
    if update_type in ['goal', 'red_card', 'penalty']:
        importance_level = "🚨 MAJOR"
    elif update_type in ['card', 'substitution']:
        importance_level = "📝 UPDATE"
    else:
        importance_level = "ℹ️ INFO"
    
    notification_title = f"{importance_level}: {notification_title}"
    
else:
    # Use standard notification creation for non-sports
    notification_title = self._create_detailed_notification_title(
        event_name, category, update_data, event_metadata
    )
    
    notification_content = self._create_detailed_notification_content(
        event_name, category, venue, update_data, event_metadata
    )
'''
    
    print("✅ Enhanced notification creation logic ready")
    print("✅ Sports events get specialized formatting")
    print("✅ Major events (goals, red cards) get priority indicators")
    print("✅ Content kept concise but informative")
    
    return enhanced_notification_code

def test_enhanced_sports_format():
    """Test what enhanced sports notifications would look like"""
    
    print("\n🧪 TESTING ENHANCED SPORTS FORMAT:")
    print("=" * 50)
    
    # Sample enhanced sports notifications
    sample_notifications = [
        {
            'title': '🚨 MAJOR: ⚽ GOAL: Johnson scores! 2-1',
            'content': '⚽ Johnson scores with right foot in the 67\' (assist: Smith) • Score: 2-1',
            'category': 'football'
        },
        {
            'title': '🚨 MAJOR: 🟥 RED CARD: Martinez sent off (78\')',
            'content': '🟥 Martinez booked for serious foul play (78\')',
            'category': 'football'
        },
        {
            'title': '📝 UPDATE: 🟨 Yellow Card: Williams (45\')',
            'content': '🟨 Williams booked for unsporting behavior (45\')',
            'category': 'football'
        },
        {
            'title': '📝 UPDATE: 🔄 SUB: Rodriguez comes on (60\')',
            'content': '🔄 Rodriguez replaces Thompson (60\')',
            'category': 'football'
        },
        {
            'title': '🚨 MAJOR: 🎯 PENALTY: Liverpool awarded (85\')',
            'content': '🎯 Penalty awarded to Liverpool for foul in box (85\')',
            'category': 'football'
        },
        {
            'title': 'ℹ️ INFO: 💥 CLOSE: Brown hits crossbar (72\')',
            'content': '💥 Brown strikes the crossbar - so close! (72\')',
            'category': 'football'
        }
    ]
    
    print("📋 SAMPLE ENHANCED SPORTS NOTIFICATIONS:")
    for i, notif in enumerate(sample_notifications, 1):
        print(f"\n   {i}. TITLE: {notif['title']}")
        print(f"      CONTENT: {notif['content']}")
        print(f"      CATEGORY: {notif['category']}")
    
    print("\n✅ BENEFITS OF ENHANCED FORMAT:")
    print("   • Quick visual recognition with emojis")
    print("   • Immediate understanding of what happened")
    print("   • Score updates included for goals")
    print("   • Player names for personal connection")
    print("   • Time stamp for context")
    print("   • Priority levels for filtering")
    print("   • Concise format perfect for Quick Updates")

def main():
    """Main enhancement process"""
    print("🏆 SPORTS UPDATE ENHANCEMENT PROCESS")
    print("=" * 60)
    
    # Check current state
    enhance_sports_update_generation()
    
    # Create enhanced functions
    enhanced_functions = create_enhanced_sports_update_functions()
    
    # Update notification creation
    enhanced_notification_code = update_sports_notification_creation()
    
    # Test the enhanced format
    test_enhanced_sports_format()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Integrate enhanced functions into live_events_manager.py")
    print("2. Update notification creation logic")
    print("3. Test with live sports events")
    print("4. Monitor Quick Updates for improved sports content")
    
    print("\n✅ SPORTS UPDATE ENHANCEMENT PLAN READY!")
    print("   Sports notifications will now show:")
    print("   • Specific action (Goal, Card, Substitution)")
    print("   • Player names and time stamps")
    print("   • Current scores for goals")
    print("   • Priority indicators for major events")
    print("   • Clean, concise format for Quick Updates")

if __name__ == "__main__":
    main()
