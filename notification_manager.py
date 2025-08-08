"""
Notification Management Module for WiseNews
Handles user notification preferences, push notifications, and email alerts
"""

import sqlite3
import json
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Tuple
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, db_path='news_database.db'):
        self.db_path = db_path
        self.vapid_public_key = "YOUR_VAPID_PUBLIC_KEY"  # Replace with actual VAPID key
        self.vapid_private_key = "YOUR_VAPID_PRIVATE_KEY"  # Replace with actual VAPID key
        
        # Email configuration (configure with your SMTP settings)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_username = "notifications@wisenews.com"  # Replace with your email
        self.email_password = "your_app_password"  # Replace with your app password
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """Get user's notification preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email_notifications, push_notifications, notification_frequency,
                   categories, keywords, sources, time_preference, timezone
            FROM notification_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'email_notifications': bool(result[0]),
                'push_notifications': bool(result[1]),
                'notification_frequency': result[2],
                'categories': json.loads(result[3]) if result[3] else [],
                'keywords': json.loads(result[4]) if result[4] else [],
                'sources': json.loads(result[5]) if result[5] else [],
                'time_preference': result[6],
                'timezone': result[7]
            }
        return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Update user's notification preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO notification_preferences 
                (user_id, email_notifications, push_notifications, notification_frequency,
                 categories, keywords, sources, time_preference, timezone, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                preferences.get('email_notifications', True),
                preferences.get('push_notifications', False),
                preferences.get('notification_frequency', 'daily'),
                json.dumps(preferences.get('categories', [])),
                json.dumps(preferences.get('keywords', [])),
                json.dumps(preferences.get('sources', [])),
                preferences.get('time_preference', '09:00'),
                preferences.get('timezone', 'UTC')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            conn.close()
            return False
    
    def subscribe_to_push(self, user_id: int, subscription_data: Dict) -> bool:
        """Subscribe user to push notifications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Deactivate existing subscriptions for this user
            cursor.execute('''
                UPDATE push_subscriptions 
                SET is_active = FALSE 
                WHERE user_id = ?
            ''', (user_id,))
            
            # Add new subscription
            cursor.execute('''
                INSERT INTO push_subscriptions 
                (user_id, endpoint, p256dh_key, auth_key, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                subscription_data['endpoint'],
                subscription_data['keys']['p256dh'],
                subscription_data['keys']['auth'],
                subscription_data.get('userAgent', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error subscribing to push: {e}")
            conn.close()
            return False
    
    def check_article_matches_preferences(self, article: Dict, preferences: Dict) -> bool:
        """Check if an article matches user's notification preferences"""
        if not preferences:
            return False
        
        # Check categories
        if preferences['categories'] and article.get('category'):
            if article['category'] not in preferences['categories']:
                return False
        
        # Check keywords
        if preferences['keywords']:
            article_text = f"{article.get('title', '')} {article.get('content', '')}".lower()
            if not any(keyword.lower() in article_text for keyword in preferences['keywords']):
                return False
        
        # Check sources
        if preferences['sources'] and article.get('source_name'):
            if article['source_name'] not in preferences['sources']:
                return False
        
        return True
    
    def queue_notification(self, user_id: int, article: Dict, notification_type: str = 'both'):
        """Queue a notification for sending"""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return
        
        if not self.check_article_matches_preferences(article, preferences):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate when to send based on frequency
        now = datetime.now()
        if preferences['notification_frequency'] == 'instant':
            scheduled_time = now
        elif preferences['notification_frequency'] == 'daily':
            # Schedule for user's preferred time
            hour, minute = map(int, preferences['time_preference'].split(':'))
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)
        elif preferences['notification_frequency'] == 'weekly':
            # Schedule for next Monday at preferred time
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:
                days_ahead += 7
            hour, minute = map(int, preferences['time_preference'].split(':'))
            scheduled_time = now + timedelta(days=days_ahead)
            scheduled_time = scheduled_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Create enhanced notification title and message
        title, message = self._create_enhanced_notification(article, preferences)
        
        # Queue email notification
        if preferences['email_notifications'] and notification_type in ['email', 'both']:
            cursor.execute('''
                INSERT INTO notification_queue 
                (user_id, article_id, notification_type, title, message, scheduled_time)
                VALUES (?, ?, 'email', ?, ?, ?)
            ''', (user_id, article['id'], title, message, scheduled_time))
        
        # Queue push notification
        if preferences['push_notifications'] and notification_type in ['push', 'both']:
            cursor.execute('''
                INSERT INTO notification_queue 
                (user_id, article_id, notification_type, title, message, scheduled_time)
                VALUES (?, ?, 'push', ?, ?, ?)
            ''', (user_id, article['id'], title, message, scheduled_time))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Queued enhanced notification for user {user_id}: {title}")
    
    def _create_enhanced_notification(self, article: Dict, preferences: Dict) -> Tuple[str, str]:
        """Create enhanced notification with detailed context and personalization"""
        category = article.get('category', 'News').title()
        source = article.get('source_name', 'Unknown Source')
        title_raw = article.get('title', 'Untitled Article')
        content_preview = article.get('content', '')[:200] + '...' if len(article.get('content', '')) > 200 else article.get('content', '')
        keywords = article.get('keywords', [])
        
        # Determine urgency and context
        urgency_indicators = ['breaking', 'urgent', 'alert', 'live', 'developing']
        is_urgent = any(indicator in title_raw.lower() for indicator in urgency_indicators)
        
        # Create personalized title
        if is_urgent:
            title = f"🚨 BREAKING: {category} Update"
        elif preferences['notification_frequency'] == 'instant':
            title = f"⚡ Fresh {category} Story - {source}"
        else:
            title = f"📰 {category} Digest - {source}"
        
        # Create comprehensive message content
        message_parts = []
        
        # Add personalized greeting based on frequency
        if preferences['notification_frequency'] == 'instant':
            message_parts.append("📱 INSTANT UPDATE:")
        elif preferences['notification_frequency'] == 'daily':
            message_parts.append("📅 YOUR DAILY BRIEFING:")
        else:
            message_parts.append("📊 WEEKLY SUMMARY:")
        
        # Add main headline with emphasis
        message_parts.append(f"\n🎯 HEADLINE: {title_raw}")
        
        # Add source credibility
        message_parts.append(f"\n📡 SOURCE: {source}")
        
        # Add content preview with context
        if content_preview:
            message_parts.append(f"\n📖 PREVIEW: {content_preview}")
        
        # Add relevance explanation based on user preferences
        relevance_reasons = []
        
        # Check category match
        if category.lower() in [cat.lower() for cat in preferences.get('categories', [])]:
            relevance_reasons.append(f"matches your {category} interest")
        
        # Check keyword matches
        user_keywords = [kw.lower() for kw in preferences.get('keywords', [])]
        matching_keywords = [kw for kw in keywords if any(uk in kw.lower() for uk in user_keywords)]
        if matching_keywords:
            relevance_reasons.append(f"contains your keywords: {', '.join(matching_keywords[:3])}")
        
        # Check source preferences
        if source in preferences.get('sources', []):
            relevance_reasons.append(f"from your preferred source: {source}")
        
        # Add relevance explanation
        if relevance_reasons:
            message_parts.append(f"\n🎯 WHY THIS MATTERS TO YOU: This story {' and '.join(relevance_reasons)}.")
        
        # Add timing context
        current_hour = datetime.now().hour
        if 6 <= current_hour < 12:
            time_context = "Perfect for your morning news catch-up! ☀️"
        elif 12 <= current_hour < 17:
            time_context = "Midday update to keep you informed! 🌞"
        elif 17 <= current_hour < 21:
            time_context = "Evening briefing for your commute! 🌅"
        else:
            time_context = "Late-night update for night owls! 🌙"
        
        message_parts.append(f"\n⏰ TIMING: {time_context}")
        
        # Add urgency context
        if is_urgent:
            message_parts.append(f"\n🚨 URGENCY: This is a developing story with potential significant impact. Stay informed as details emerge.")
        
        # Add category-specific context
        category_context = self._get_category_context(category, title_raw, keywords)
        if category_context:
            message_parts.append(f"\n📊 IMPACT: {category_context}")
        
        # Add follow-up suggestions
        if preferences['notification_frequency'] == 'instant':
            message_parts.append(f"\n👆 NEXT STEPS: Tap to read the full story and stay ahead of the news!")
        else:
            message_parts.append(f"\n📚 EXPLORE MORE: Check your WiseNews dashboard for more stories in your areas of interest!")
        
        # Add subscription value reminder
        if is_urgent or preferences['notification_frequency'] == 'instant':
            message_parts.append(f"\n✨ PREMIUM BENEFIT: You're getting this instant update because of your Premium subscription!")
        
        return title, ''.join(message_parts)
    
    def _get_category_context(self, category: str, title: str, keywords: List[str]) -> str:
        """Generate category-specific context for notifications"""
        category_lower = category.lower()
        title_lower = title.lower()
        
        if category_lower in ['politics', 'government']:
            if any(word in title_lower for word in ['election', 'vote', 'campaign']):
                return "This political development could influence upcoming electoral processes and policy decisions."
            elif any(word in title_lower for word in ['policy', 'law', 'regulation']):
                return "This policy change may affect regulatory frameworks and citizen rights."
            else:
                return "This political news could have implications for governance and public policy."
        
        elif category_lower in ['technology', 'tech']:
            if any(word in title_lower for word in ['ai', 'artificial intelligence', 'machine learning']):
                return "This AI development could reshape technology applications and industry standards."
            elif any(word in title_lower for word in ['crypto', 'bitcoin', 'blockchain']):
                return "This cryptocurrency news may impact digital asset markets and regulatory approaches."
            else:
                return "This technology update could influence digital innovation and market trends."
        
        elif category_lower in ['business', 'finance', 'economy']:
            if any(word in title_lower for word in ['earnings', 'quarterly', 'revenue', 'profit']):
                return "These financial results may influence company valuations, investor sentiment, and sector-wide performance metrics."
            elif any(word in title_lower for word in ['acquisition', 'merger', 'deal', 'buyout']):
                return "This M&A activity could reshape competitive dynamics, create market consolidation, and influence strategic positioning across the industry."
            elif any(word in title_lower for word in ['ceo', 'leadership', 'executive', 'management']):
                return "This leadership development may impact corporate strategy, operational execution, and investor confidence in the company's direction."
            elif any(word in title_lower for word in ['product', 'launch', 'innovation', 'technology']):
                return "This product development could drive revenue growth, enhance competitive positioning, and influence market share dynamics."
            elif any(word in title_lower for word in ['stock', 'market', 'trading']):
                return "This market news could affect investment decisions and portfolio performance."
            else:
                return "This business development could impact economic trends and market conditions."
        
        elif category_lower in ['health', 'medical']:
            if any(word in title_lower for word in ['covid', 'pandemic', 'vaccine']):
                return "This health update may affect public health policies and safety measures."
            else:
                return "This health news could influence medical practices and patient care."
        
        elif category_lower in ['sports']:
            if any(word in title_lower for word in ['championship', 'final', 'playoff']):
                return "This major sporting event could determine championship outcomes and legacy records."
            else:
                return "This sports update may affect team standings and upcoming match dynamics."
        
        elif category_lower in ['entertainment']:
            return "This entertainment news reflects current cultural trends and audience preferences."
        
        else:
            return "This story contributes to your comprehensive understanding of current events."
    
    def send_email_notification(self, user_email: str, title: str, message: str, article_url: str = None):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = user_email
            msg['Subject'] = title
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 24px;">📰 WiseNews</h1>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #2c3e50; margin-top: 0;">{title}</h2>
                            <p style="font-size: 16px; margin-bottom: 20px;">{message}</p>
                            
                            {f'<a href="{article_url}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Read Full Article</a>' if article_url else ''}
                            
                            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                            
                            <p style="font-size: 14px; color: #666;">
                                You're receiving this because you've subscribed to WiseNews notifications.
                                <br>
                                <a href="http://wisenews.app/notification-preferences" style="color: #007bff;">Manage your notification preferences</a> |
                                <a href="http://wisenews.app/unsubscribe" style="color: #007bff;">Unsubscribe</a>
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_push_notification(self, user_id: int, title: str, message: str, article_url: str = None):
        """Send push notification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active push subscriptions for user
        cursor.execute('''
            SELECT endpoint, p256dh_key, auth_key
            FROM push_subscriptions
            WHERE user_id = ? AND is_active = TRUE
        ''', (user_id,))
        
        subscriptions = cursor.fetchall()
        conn.close()
        
        if not subscriptions:
            logger.info(f"No active push subscriptions for user {user_id}")
            return False
        
        payload = {
            'title': title,
            'body': message,
            'icon': '/static/icon-192.png',
            'badge': '/static/badge-72.png',
            'url': article_url or '/dashboard',
            'data': {
                'url': article_url or '/dashboard'
            }
        }
        
        success_count = 0
        for endpoint, p256dh, auth in subscriptions:
            try:
                # Here you would use a push notification library like py-vapid
                # For now, this is a placeholder for the actual implementation
                logger.info(f"Would send push notification to {endpoint}")
                success_count += 1
            except Exception as e:
                logger.error(f"Error sending push notification: {e}")
        
        return success_count > 0
    
    def process_notification_queue(self):
        """Process pending notifications in the queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pending notifications that are ready to be sent
        cursor.execute('''
            SELECT nq.id, nq.user_id, nq.article_id, nq.notification_type, 
                   nq.title, nq.message, u.email, a.id as article_id
            FROM notification_queue nq
            JOIN users u ON nq.user_id = u.id
            LEFT JOIN articles a ON nq.article_id = a.id
            WHERE nq.status = 'pending' 
            AND nq.scheduled_time <= CURRENT_TIMESTAMP
            ORDER BY nq.scheduled_time ASC
            LIMIT 50
        ''')
        
        notifications = cursor.fetchall()
        
        for notification in notifications:
            queue_id, user_id, article_id, notif_type, title, message, user_email, _ = notification
            
            success = False
            article_url = f"http://wisenews.app/article/{article_id}" if article_id else None
            
            if notif_type == 'email':
                success = self.send_email_notification(user_email, title, message, article_url)
            elif notif_type == 'push':
                success = self.send_push_notification(user_id, title, message, article_url)
            
            # Update queue status
            if success:
                cursor.execute('''
                    UPDATE notification_queue 
                    SET status = 'sent', sent_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (queue_id,))
                
                # Add to notification history
                cursor.execute('''
                    INSERT INTO notification_history 
                    (user_id, notification_type, title, message, article_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, notif_type, title, message, article_id))
            else:
                # Increment retry count
                cursor.execute('''
                    UPDATE notification_queue 
                    SET retry_count = retry_count + 1,
                        status = CASE WHEN retry_count >= 3 THEN 'failed' ELSE 'pending' END
                    WHERE id = ?
                ''', (queue_id,))
        
        conn.commit()
        conn.close()
        
        return len(notifications)
    
    def get_notification_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's notification history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT notification_type, title, message, sent_time, read_status, article_id
            FROM notification_history
            WHERE user_id = ?
            ORDER BY sent_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'type': row[0],
                'title': row[1],
                'message': row[2],
                'sent_time': row[3],
                'read': bool(row[4]),
                'article_id': row[5]
            })
        
        conn.close()
        return history
    
    def mark_notification_read(self, user_id: int, notification_id: int):
        """Mark a notification as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notification_history 
            SET read_status = TRUE
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_available_categories(self) -> List[str]:
        """Get all available article categories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT category 
            FROM articles 
            WHERE category IS NOT NULL 
            ORDER BY category
        ''')
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
    
    def get_available_sources(self) -> List[str]:
        """Get all available news sources"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT source_name 
            FROM articles 
            WHERE source_name IS NOT NULL 
            ORDER BY source_name
        ''')
        
        sources = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sources

def start_notification_processor():
    """Start the background notification processor"""
    def processor():
        notification_manager = NotificationManager()
        while True:
            try:
                processed = notification_manager.process_notification_queue()
                if processed > 0:
                    logger.info(f"Processed {processed} notifications")
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")
                time.sleep(60)
    
    thread = threading.Thread(target=processor, daemon=True)
    thread.start()
    logger.info("Notification processor started")
