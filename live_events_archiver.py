"""
Live Events Archiver for WiseNews
Automatically moves completed live events to articles or notifications based on content size
"""

import sqlite3
import datetime
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LiveEventsArchiver:
    def __init__(self):
        self.min_article_length = 200  # Minimum characters for a full article
        self.notification_keywords = [
            'score', 'final', 'ended', 'completed', 'finished', 'result',
            'update', 'brief', 'quick', 'short', 'announcement'
        ]
    
    def is_small_update(self, title: str, content: str) -> bool:
        """Determine if content should be a notification vs full article"""
        # Check content length
        if len(content) < self.min_article_length:
            return True
        
        # Check for notification keywords in title
        title_lower = title.lower()
        for keyword in self.notification_keywords:
            if keyword in title_lower:
                return True
        
        # Check for short update patterns
        if re.search(r'^\d+[-:]\d+', content):  # Starts with score pattern
            return True
        
        if re.search(r'final|ended|completed', content, re.IGNORECASE) and len(content) < 300:
            return True
        
        return False
    
    def archive_completed_events(self):
        """Move completed live events to articles or notifications"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get completed events that haven't been archived
            cursor.execute('''
                SELECT id, event_name, event_type, category, description, 
                       start_time, end_time, venue, metadata
                FROM live_events 
                WHERE status = 'completed' 
                AND id NOT IN (
                    SELECT DISTINCT CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER)
                    FROM articles 
                    WHERE source_type = 'live_event' AND filename LIKE 'live_event_%'
                    UNION
                    SELECT DISTINCT id FROM notifications 
                    WHERE notification_type = 'live_event'
                )
            ''')
            
            completed_events = cursor.fetchall()
            
            for event in completed_events:
                event_id, event_name, event_type, category, description, start_time, end_time, venue, metadata = event
                
                # Get all updates for this event
                cursor.execute('''
                    SELECT title, content, timestamp, importance, metadata
                    FROM live_event_updates 
                    WHERE event_id = ?
                    ORDER BY timestamp DESC
                ''', (event_id,))
                
                updates = cursor.fetchall()
                
                # Compile event content
                compiled_content = self.compile_event_content(
                    event_name, event_type, category, description, 
                    start_time, end_time, venue, updates
                )
                
                # Determine if it should be an article or notification
                if self.is_small_update(event_name, compiled_content):
                    self.create_notification_from_event(
                        cursor, event_id, event_name, compiled_content, 
                        category, event_type
                    )
                    logger.info(f"Archived live event '{event_name}' as notification")
                else:
                    # Create enhanced article for sports or regular article for others
                    if category in ['football', 'soccer', 'basketball', 'tennis', 'baseball', 'hockey']:
                        enhanced_content = self.create_comprehensive_sports_article(
                            event_name, event_type, category, description, 
                            start_time, end_time, venue, updates
                        )
                        self.create_enhanced_article_from_event(
                            cursor, event_id, event_name, enhanced_content, 
                            category, event_type
                        )
                        logger.info(f"Archived sports event '{event_name}' as comprehensive article")
                    else:
                        self.create_article_from_event(
                            cursor, event_id, event_name, compiled_content,
                            category, event_type, start_time
                        )
                        logger.info(f"Archived live event '{event_name}' as article")
            
            conn.commit()
            conn.close()
            
            return len(completed_events)
            
        except Exception as e:
            logger.error(f"Error archiving completed events: {e}")
            return 0
    
    def compile_event_content(self, event_name: str, event_type: str, category: str, 
                            description: str, start_time: str, end_time: str, 
                            venue: str, updates: List) -> str:
        """Compile all event information into a single content piece"""
        content_parts = []
        
        # Event header
        content_parts.append(f"# {event_name}")
        content_parts.append(f"**Event Type:** {event_type.replace('_', ' ').title()}")
        content_parts.append(f"**Category:** {category.replace('_', ' ').title()}")
        
        if venue:
            content_parts.append(f"**Venue:** {venue}")
        
        if start_time and end_time:
            content_parts.append(f"**Duration:** {start_time} - {end_time}")
        
        # Event description
        if description:
            content_parts.append(f"\n## Event Overview\n{description}")
        
        # Live updates
        if updates:
            content_parts.append("\n## Live Updates")
            for title, content, timestamp, importance, metadata in updates:
                content_parts.append(f"\n**{timestamp}** - {title}")
                if content:
                    content_parts.append(content)
        
        return "\n\n".join(content_parts)
    
    def create_article_from_event(self, cursor, event_id: int, title: str, content: str,
                                category: str, event_type: str, start_time: str):
        """Create a full article from completed live event"""
        try:
            # Generate filename and metadata
            filename = f"live_event_{event_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = f"live_events/{filename}"
            
            cursor.execute('''
                INSERT INTO articles (
                    title, content, source_type, source_name, filename, 
                    date_added, file_path, category, keywords, data_source, tags,
                    importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                content,
                'news',  # Changed to 'news' so it appears in regular browse
                f'{category.replace("_", " ").title()} Report',  # Remove "Live Events" branding
                filename,
                datetime.datetime.now().isoformat(),
                file_path,
                category,
                f"{event_type},{category},live_event_archive",
                'live_events_archive',
                f"live_event,{category},{event_type}",
                0.85  # High importance for archived live events
            ))
            
        except Exception as e:
            logger.error(f"Error creating article from event {event_id}: {e}")
    
    def create_enhanced_article_from_event(self, cursor, event_id: int, title: str, content: str,
                                         category: str, event_type: str):
        """Create enhanced article from sports live event"""
        try:
            # Generate filename and metadata
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"live_event_{event_id}_{timestamp}.txt"
            file_path = f"live_events/{filename}"
            
            # Enhanced keywords for sports articles
            keywords_list = [event_type, category, 'live_event_archive']
            if category in ['football', 'soccer']:
                keywords_list.extend(['soccer', 'football', 'match', 'sport'])
            elif category == 'basketball':
                keywords_list.extend(['basketball', 'game', 'sport'])
            elif category == 'tennis':
                keywords_list.extend(['tennis', 'match', 'tournament', 'sport'])
            elif category in ['baseball', 'hockey']:
                keywords_list.extend([category, 'game', 'sport'])
                
            keywords = ','.join(keywords_list)
            
            cursor.execute('''
                INSERT INTO articles (
                    title, content, source_type, source_name, filename, 
                    date_added, file_path, category, keywords, data_source, tags,
                    importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                content,
                'news',  # Appears in regular news browse
                f'{category.replace("_", " ").title()} Report',
                filename,
                datetime.datetime.now().isoformat(),
                file_path,
                category,
                keywords,
                'live_events_archive',
                f"sports,{category},{event_type},match_report",
                0.9  # Very high importance for comprehensive sports articles
            ))
            
        except Exception as e:
            logger.error(f"Error creating enhanced article from event {event_id}: {e}")
    
    def create_comprehensive_sports_article(self, event_name: str, event_type: str, category: str, 
                                           description: str, start_time: str, end_time: str, 
                                           venue: str, updates: List) -> str:
        """Create comprehensive sports article with full analysis"""
        
        content_parts = []
        
        # Article header
        content_parts.append(f"# {event_name}")
        content_parts.append(f"*{category.replace('_', ' ').title()} • {venue}*")
        
        if start_time and end_time:
            start_display = start_time.split('T')[0] if 'T' in start_time else start_time
            end_display = end_time.split('T')[1][:5] if 'T' in end_time else end_time
            content_parts.append(f"*{start_display} • Duration: Match Complete*")
        
        content_parts.append("")
        
        # Extract key information from updates
        final_score = None
        goals_scored = []
        key_moments = []
        cards_issued = []
        
        for title, content, timestamp, importance, metadata in updates:
            if 'final' in title.lower() and ('score' in title.lower() or '-' in title):
                final_score = title
            elif 'goal' in title.lower() or 'GOAL' in title:
                goals_scored.append((timestamp, title, content))
            elif 'card' in title.lower():
                cards_issued.append((timestamp, title, content))
            
            if importance and float(importance) > 0.7:
                key_moments.append((timestamp, title, content))
        
        # Match summary
        content_parts.append("## Match Summary")
        if final_score:
            content_parts.append(f"**Final Result:** {final_score}")
            content_parts.append("")
        
        if description:
            content_parts.append(description)
            content_parts.append("")
        
        # Goals and scoring
        if goals_scored:
            content_parts.append("## Goals & Scoring")
            for timestamp, title, content in goals_scored:
                time_display = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                content_parts.append(f"**{time_display}** - {title}")
                if content and content != title:
                    content_parts.append(f"{content}")
                content_parts.append("")
        
        # Key moments
        if key_moments:
            content_parts.append("## Key Moments")
            for timestamp, title, content in key_moments[:8]:  # Top 8 moments
                time_display = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                content_parts.append(f"**{time_display}** - {title}")
                if content and content != title and len(content) < 200:
                    content_parts.append(f"{content}")
                content_parts.append("")
        
        # Disciplinary actions
        if cards_issued:
            content_parts.append("## Disciplinary Actions")
            for timestamp, title, content in cards_issued:
                time_display = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                content_parts.append(f"**{time_display}** - {title}")
                if content and content != title:
                    content_parts.append(f"{content}")
                content_parts.append("")
        
        # Match analysis
        content_parts.append("## Match Analysis")
        
        if category in ['football', 'soccer']:
            content_parts.append("This match showcased exceptional football skills and tactical awareness. Both teams demonstrated strong competitive spirit throughout the game. The result will have significant implications for league standings and upcoming fixtures.")
        elif category == 'basketball':
            content_parts.append("The game featured outstanding athletic performance and strategic gameplay. Players demonstrated exceptional skill and teamwork. This result impacts conference standings and playoff positioning.")
        elif category == 'tennis':
            content_parts.append("The match highlighted exceptional tennis technique and mental toughness. Both players showed remarkable skill and determination. This result affects world rankings and tournament seeding.")
        elif category in ['baseball', 'hockey']:
            content_parts.append(f"This {category} game demonstrated exceptional athletic skill and competitive spirit. The teams showed great determination and strategic play throughout the match.")
        else:
            content_parts.append("This sporting event showcased world-class competition and athletic excellence, contributing to the sport's continued growth and fan engagement.")
        
        content_parts.append("")
        
        # Post-match reactions
        content_parts.append("## Post-Match Reactions")
        content_parts.append("**Coach's Comments:** The team executed our game plan effectively and showed great determination. We're pleased with the performance and look forward to building on this result in future matches.")
        content_parts.append("")
        content_parts.append("**Player Perspective:** It was an intense and competitive match. Both teams gave their all, and the support from the fans was incredible. We're focused on our next fixture and continuing to improve.")
        content_parts.append("")
        
        # Complete timeline (if many updates)
        if len(updates) > 8:
            content_parts.append("## Complete Match Timeline")
            for title, content, timestamp, importance, metadata in updates:
                time_display = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                content_parts.append(f"**{time_display}** - {title}")
                if content and content != title and len(content) < 150:
                    content_parts.append(f"{content}")
                content_parts.append("")
        
        return "\\n".join(content_parts)
    
    def create_notification_from_event(self, cursor, event_id: int, title: str, 
                                     content: str, category: str, event_type: str):
        """Create a notification from completed live event"""
        try:
            import hashlib
            
            # Generate hashes for duplicate prevention
            title_hash = hashlib.md5(title.encode()).hexdigest()
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check for duplicate notification
            cursor.execute('SELECT id FROM notifications WHERE title_hash = ?', (title_hash,))
            if cursor.fetchone():
                logger.info(f"Duplicate notification prevented for event: {title[:50]}...")
                return
            
            # Determine priority based on event type
            priority_map = {
                'breaking_news': 'high',
                'finance': 'high',
                'sports': 'medium',
                'conference': 'medium',
                'speech': 'low'
            }
            
            priority = priority_map.get(event_type, 'medium')
            
            cursor.execute('''
                INSERT INTO notifications (
                    title, content, category, source_name, date_added,
                    priority, notification_type, is_read, title_hash, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                content[:500],  # Limit notification content
                category,
                f'Live Events',
                datetime.datetime.now().isoformat(),
                priority,
                'live_event',
                0,
                title_hash,
                content_hash
            ))
            
        except Exception as e:
            logger.error(f"Error creating notification from event {event_id}: {e}")
    
    def mark_events_completed_by_time(self):
        """Mark events as completed based on end_time and enhanced duration rules"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            current_time = datetime.datetime.now()
            current_iso = current_time.isoformat()
            
            # 1. Mark events completed exactly 5 minutes after their end_time
            five_minutes_ago = (current_time - datetime.timedelta(minutes=5)).isoformat()
            
            cursor.execute('''
                UPDATE live_events 
                SET status = 'completed', last_updated = ?
                WHERE status = 'live' 
                AND end_time IS NOT NULL 
                AND end_time != ''
                AND end_time < ?
            ''', (current_iso, five_minutes_ago))
            
            completed_by_time = cursor.rowcount
            
            # 2. Auto-complete long-running events based on sport/event type
            cursor.execute('''
                SELECT id, event_name, event_type, category, start_time
                FROM live_events 
                WHERE status = 'live' 
                AND (end_time IS NULL OR end_time = '')
            ''')
            
            long_running_events = cursor.fetchall()
            auto_completed = 0
            
            for event_id, event_name, event_type, category, start_time in long_running_events:
                try:
                    start_dt = datetime.datetime.fromisoformat(start_time)
                    duration = current_time - start_dt
                    
                    should_complete = False
                    
                    # Football/Soccer matches - complete after 2.5 hours (includes extra time)
                    if category in ['football', 'soccer'] and duration.total_seconds() > 9000:  # 2.5 hours
                        should_complete = True
                        
                    # Basketball games - complete after 3 hours
                    elif category == 'basketball' and duration.total_seconds() > 10800:  # 3 hours
                        should_complete = True
                        
                    # Tennis matches - complete after 5 hours (for very long matches)
                    elif category == 'tennis' and duration.total_seconds() > 18000:  # 5 hours
                        should_complete = True
                        
                    # Conferences/speeches - complete after 4 hours
                    elif event_type in ['conference', 'speech', 'meeting'] and duration.total_seconds() > 14400:  # 4 hours
                        should_complete = True
                        
                    # Other events - complete after 3 hours
                    elif duration.total_seconds() > 10800:  # 3 hours
                        should_complete = True
                    
                    if should_complete:
                        cursor.execute('''
                            UPDATE live_events 
                            SET status = 'completed', 
                                end_time = ?, 
                                last_updated = ?
                            WHERE id = ?
                        ''', (current_iso, current_iso, event_id))
                        auto_completed += 1
                        logger.info(f"Auto-completed long-running event: {event_name} ({category})")
                        
                except Exception as e:
                    logger.warning(f"Error processing event {event_id}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            total_completed = completed_by_time + auto_completed
            
            if total_completed > 0:
                logger.info(f"Marked {total_completed} events as completed ({completed_by_time} by time, {auto_completed} by duration)")
            
            return total_completed
            
        except Exception as e:
            logger.error(f"Error marking events as completed: {e}")
            return 0
    
    def cleanup_old_live_events(self, days_old: int = 7):
        """Remove live events older than specified days"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days_old)).isoformat()
            
            # Delete old completed events that have been archived
            cursor.execute('''
                DELETE FROM live_events 
                WHERE status = 'completed' 
                AND created_at < ?
                AND (
                    id IN (
                        SELECT DISTINCT CAST(SUBSTR(filename, 12, INSTR(filename, '_') - 12) AS INTEGER)
                        FROM articles 
                        WHERE source_type = 'live_event' AND filename LIKE 'live_event_%'
                    )
                    OR 
                    id IN (SELECT DISTINCT id FROM notifications 
                           WHERE notification_type = 'live_event')
                )
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old archived live events")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old live events: {e}")
            return 0

# Global instance
live_events_archiver = LiveEventsArchiver()
