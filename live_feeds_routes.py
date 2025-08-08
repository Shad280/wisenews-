"""
Live Feeds Routes for WiseNews
Real-time data feeds interface for users
"""

from flask import Blueprint, render_template, request, jsonify, session
from scraper_protection import anti_scraper_protection
from auth_decorators import login_required, get_current_user
import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create blueprint
live_feeds_bp = Blueprint('live_feeds', __name__)

@live_feeds_bp.route('/live-feeds')
@login_required
def live_feeds_dashboard():
    """Live feeds dashboard for users"""
    try:
        user = get_current_user()
        
        # Get user preferences
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT feed_types, keywords, notification_enabled 
            FROM user_live_preferences 
            WHERE user_id = ?
        ''', (user['user_id'],))
        
        preferences = cursor.fetchone()
        if preferences:
            user_feed_types = preferences[0].split(',') if preferences[0] else []
            user_keywords = preferences[1].split(',') if preferences[1] else []
            notifications_enabled = preferences[2]
        else:
            user_feed_types = ['news', 'financial', 'crypto']
            user_keywords = []
            notifications_enabled = True
        
        # Get recent live feeds
        recent_feeds = get_recent_live_feeds(feed_types=user_feed_types, limit=50)
        
        # Get feed statistics
        feed_stats = get_live_feed_statistics()
        
        conn.close()
        
        return render_template('live_feeds.html',
                             recent_feeds=recent_feeds,
                             feed_stats=feed_stats,
                             user_feed_types=user_feed_types,
                             user_keywords=user_keywords,
                             notifications_enabled=notifications_enabled)
                             
    except Exception as e:
        logger.error(f"Error in live feeds dashboard: {e}")
        return render_template('error.html', error="Failed to load live feeds")

@live_feeds_bp.route('/api/live-feeds')
@anti_scraper_protection
def api_live_feeds():
    """API endpoint for live feeds data"""
    try:
        # Get parameters
        feed_types = request.args.get('types', '').split(',') if request.args.get('types') else None
        limit = min(int(request.args.get('limit', 20)), 100)
        since = request.args.get('since')  # ISO timestamp
        importance_min = int(request.args.get('importance_min', 1))
        
        # Build query
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        conditions = ['importance_score >= ?']
        params = [importance_min]
        
        if feed_types and feed_types != ['']:
            placeholders = ','.join(['?' for _ in feed_types])
            conditions.append(f'feed_type IN ({placeholders})')
            params.extend(feed_types)
        
        if since:
            conditions.append('timestamp > ?')
            params.append(since)
        
        query = f'''
            SELECT id, feed_type, source, title, content, timestamp, 
                   importance_score, tags, is_breaking, user_views
            FROM live_feeds 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        params.append(limit)
        
        cursor.execute(query, params)
        feeds = cursor.fetchall()
        
        # Format response
        response_data = []
        for feed in feeds:
            response_data.append({
                'id': feed[0],
                'feed_type': feed[1],
                'source': feed[2],
                'title': feed[3],
                'content': feed[4],
                'timestamp': feed[5],
                'importance_score': feed[6],
                'tags': feed[7].split(',') if feed[7] else [],
                'is_breaking': bool(feed[8]),
                'user_views': feed[9]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'feeds': response_data,
            'count': len(response_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in live feeds API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_feeds_bp.route('/api/live-feeds/breaking')
@anti_scraper_protection
def api_breaking_news():
    """API for breaking news only"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, feed_type, source, title, content, timestamp, importance_score
            FROM live_feeds 
            WHERE is_breaking = 1 AND timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        
        breaking_feeds = cursor.fetchall()
        conn.close()
        
        response_data = []
        for feed in breaking_feeds:
            response_data.append({
                'id': feed[0],
                'feed_type': feed[1],
                'source': feed[2],
                'title': feed[3],
                'content': feed[4],
                'timestamp': feed[5],
                'importance_score': feed[6]
            })
        
        return jsonify({
            'success': True,
            'breaking_news': response_data,
            'count': len(response_data)
        })
        
    except Exception as e:
        logger.error(f"Error in breaking news API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_feeds_bp.route('/api/live-feeds/subscribe', methods=['POST'])
@login_required
def subscribe_to_feed():
    """Subscribe user to specific live feed"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        feed_id = data.get('feed_id')
        if not feed_id:
            return jsonify({'success': False, 'error': 'Feed ID required'}), 400
        
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Check if already subscribed
        cursor.execute('''
            SELECT id FROM live_feed_subscriptions 
            WHERE user_id = ? AND feed_id = ?
        ''', (user['user_id'], feed_id))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Already subscribed'})
        
        # Add subscription
        cursor.execute('''
            INSERT INTO live_feed_subscriptions (user_id, feed_id)
            VALUES (?, ?)
        ''', (user['user_id'], feed_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Subscribed successfully'})
        
    except Exception as e:
        logger.error(f"Error subscribing to feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_feeds_bp.route('/api/live-feeds/preferences', methods=['GET', 'POST'])
@login_required
def manage_feed_preferences():
    """Get or update user feed preferences"""
    try:
        user = get_current_user()
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('''
                SELECT feed_types, keywords, notification_enabled 
                FROM user_live_preferences 
                WHERE user_id = ?
            ''', (user['user_id'],))
            
            preferences = cursor.fetchone()
            if preferences:
                response = {
                    'feed_types': preferences[0].split(',') if preferences[0] else [],
                    'keywords': preferences[1].split(',') if preferences[1] else [],
                    'notification_enabled': bool(preferences[2])
                }
            else:
                response = {
                    'feed_types': ['news', 'financial', 'crypto'],
                    'keywords': [],
                    'notification_enabled': True
                }
            
            conn.close()
            return jsonify({'success': True, 'preferences': response})
        
        elif request.method == 'POST':
            data = request.get_json()
            
            feed_types = ','.join(data.get('feed_types', []))
            keywords = ','.join(data.get('keywords', []))
            notification_enabled = data.get('notification_enabled', True)
            
            # Insert or update preferences
            cursor.execute('''
                INSERT OR REPLACE INTO user_live_preferences 
                (user_id, feed_types, keywords, notification_enabled)
                VALUES (?, ?, ?, ?)
            ''', (user['user_id'], feed_types, keywords, notification_enabled))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Preferences updated'})
            
    except Exception as e:
        logger.error(f"Error managing feed preferences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_feeds_bp.route('/api/live-feeds/mark-viewed', methods=['POST'])
@login_required
def mark_feed_viewed():
    """Mark feed as viewed by user"""
    try:
        data = request.get_json()
        feed_id = data.get('feed_id')
        
        if not feed_id:
            return jsonify({'success': False, 'error': 'Feed ID required'}), 400
        
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE live_feeds 
            SET user_views = user_views + 1 
            WHERE id = ?
        ''', (feed_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error marking feed as viewed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@live_feeds_bp.route('/api/live-feeds/stats')
@anti_scraper_protection
def api_feed_stats():
    """Get live feeds statistics"""
    try:
        stats = get_live_feed_statistics()
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Error getting feed stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_recent_live_feeds(feed_types=None, limit=50):
    """Get recent live feeds from database"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        if feed_types and len(feed_types) > 0:
            placeholders = ','.join(['?' for _ in feed_types])
            query = f'''
                SELECT id, feed_type, source, title, content, timestamp, 
                       importance_score, tags, is_breaking, user_views
                FROM live_feeds 
                WHERE feed_type IN ({placeholders})
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            cursor.execute(query, feed_types + [limit])
        else:
            cursor.execute('''
                SELECT id, feed_type, source, title, content, timestamp, 
                       importance_score, tags, is_breaking, user_views
                FROM live_feeds 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        feeds = cursor.fetchall()
        conn.close()
        
        return [{
            'id': feed[0],
            'feed_type': feed[1],
            'source': feed[2],
            'title': feed[3],
            'content': feed[4],
            'timestamp': feed[5],
            'importance_score': feed[6],
            'tags': feed[7].split(',') if feed[7] else [],
            'is_breaking': bool(feed[8]),
            'user_views': feed[9]
        } for feed in feeds]
        
    except Exception as e:
        logger.error(f"Error getting recent live feeds: {e}")
        return []

def get_live_feed_statistics():
    """Get live feed statistics"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Total feeds today
        cursor.execute('''
            SELECT COUNT(*) FROM live_feeds 
            WHERE date(timestamp) = date('now')
        ''')
        today_count = cursor.fetchone()[0]
        
        # Breaking news count
        cursor.execute('''
            SELECT COUNT(*) FROM live_feeds 
            WHERE is_breaking = 1 AND timestamp > datetime('now', '-24 hours')
        ''')
        breaking_count = cursor.fetchone()[0]
        
        # Feed types count
        cursor.execute('''
            SELECT feed_type, COUNT(*) FROM live_feeds 
            WHERE date(timestamp) = date('now')
            GROUP BY feed_type
        ''')
        feed_types = dict(cursor.fetchall())
        
        # Most active sources
        cursor.execute('''
            SELECT source, COUNT(*) FROM live_feeds 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY source 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        active_sources = cursor.fetchall()
        
        conn.close()
        
        return {
            'today_count': today_count,
            'breaking_count': breaking_count,
            'feed_types': feed_types,
            'active_sources': active_sources
        }
        
    except Exception as e:
        logger.error(f"Error getting feed statistics: {e}")
        return {
            'today_count': 0,
            'breaking_count': 0,
            'feed_types': {},
            'active_sources': []
        }
