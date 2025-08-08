"""
Enhanced Live Events System for WiseNews
Real-time improvements with WebSocket support, better performance, and enhanced features
"""

import asyncio
import websockets
import json
import time
import sqlite3
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class EnhancedLiveEventsManager:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.event_rooms = {}  # event_id -> set of session_ids
        self.user_subscriptions = {}  # user_id -> set of event_ids
        self.event_queue = queue.Queue()
        self.performance_metrics = {
            'total_updates': 0,
            'avg_response_time': 0,
            'active_connections': 0,
            'events_per_minute': 0
        }
        
        # Initialize WebSocket handlers
        self._setup_websocket_handlers()
        
        # Start background processors
        self._start_background_processors()
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('join_event')
        def handle_join_event(data):
            event_id = data.get('event_id')
            user_id = data.get('user_id')
            
            if not event_id or not user_id:
                emit('error', {'message': 'Invalid event or user ID'})
                return
            
            # Join the event room
            room = f"event_{event_id}"
            join_room(room)
            
            # Track room membership
            if event_id not in self.event_rooms:
                self.event_rooms[event_id] = set()
            self.event_rooms[event_id].add(request.sid)
            
            # Track user subscriptions
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(event_id)
            
            # Update metrics
            self.performance_metrics['active_connections'] += 1
            
            # Send confirmation and initial event data
            emit('joined_event', {
                'event_id': event_id,
                'status': 'connected',
                'timestamp': datetime.now().isoformat()
            })
            
            # Send recent updates
            recent_updates = self._get_recent_updates(event_id, limit=5)
            emit('initial_updates', {'updates': recent_updates})
            
            logger.info(f"User {user_id} joined live event {event_id}")
        
        @self.socketio.on('leave_event')
        def handle_leave_event(data):
            event_id = data.get('event_id')
            user_id = data.get('user_id')
            
            room = f"event_{event_id}"
            leave_room(room)
            
            # Update tracking
            if event_id in self.event_rooms:
                self.event_rooms[event_id].discard(request.sid)
            
            if user_id in self.user_subscriptions:
                self.user_subscriptions[user_id].discard(event_id)
            
            self.performance_metrics['active_connections'] -= 1
            
            emit('left_event', {'event_id': event_id, 'status': 'disconnected'})
            logger.info(f"User {user_id} left live event {event_id}")
        
        @self.socketio.on('request_event_status')
        def handle_event_status(data):
            event_id = data.get('event_id')
            status = self._get_event_status(event_id)
            emit('event_status', status)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            # Clean up user connections
            session_id = request.sid
            for event_id, sessions in self.event_rooms.items():
                sessions.discard(session_id)
            
            self.performance_metrics['active_connections'] -= 1
            logger.info(f"User disconnected: {session_id}")
    
    def _start_background_processors(self):
        """Start background threads for processing"""
        
        # Event update processor
        def process_event_updates():
            while True:
                try:
                    if not self.event_queue.empty():
                        event_data = self.event_queue.get(timeout=1)
                        self._broadcast_event_update(event_data)
                        self.performance_metrics['total_updates'] += 1
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing event update: {e}")
        
        # Performance metrics calculator
        def calculate_metrics():
            import time  # Ensure time is available in this scope
            last_update_count = 0
            while True:
                try:
                    time.sleep(60)  # Update every minute
                    current_updates = self.performance_metrics['total_updates']
                    self.performance_metrics['events_per_minute'] = current_updates - last_update_count
                    last_update_count = current_updates
                except Exception as e:
                    logger.error(f"Error calculating metrics: {e}")
        
        # Start threads
        threading.Thread(target=process_event_updates, daemon=True).start()
        threading.Thread(target=calculate_metrics, daemon=True).start()
    
    def add_event_update(self, event_id, update_data):
        """Add a new event update to the queue"""
        enhanced_update = {
            'event_id': event_id,
            'timestamp': datetime.now().isoformat(),
            'data': update_data,
            'priority': update_data.get('priority', 'normal'),
            'update_type': update_data.get('type', 'general')
        }
        
        self.event_queue.put(enhanced_update)
    
    def _broadcast_event_update(self, event_data):
        """Broadcast update to all subscribers of an event"""
        event_id = event_data['event_id']
        room = f"event_{event_id}"
        
        # Enhanced update with metadata
        broadcast_data = {
            'event_id': event_id,
            'update': event_data['data'],
            'timestamp': event_data['timestamp'],
            'update_type': event_data.get('update_type', 'general'),
            'priority': event_data.get('priority', 'normal'),
            'sequence_number': self.performance_metrics['total_updates']
        }
        
        # Broadcast to WebSocket room
        self.socketio.emit('live_update', broadcast_data, room=room)
        
        # Log for analytics
        logger.info(f"Broadcasted update for event {event_id} to {len(self.event_rooms.get(event_id, []))} clients")
    
    def _get_recent_updates(self, event_id, limit=10):
        """Get recent updates for an event"""
        try:
            import sqlite3
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT update_text, update_time, update_type, metadata
                FROM live_event_updates 
                WHERE event_id = ?
                ORDER BY update_time DESC
                LIMIT ?
            ''', (event_id, limit))
            
            updates = []
            for row in cursor.fetchall():
                updates.append({
                    'text': row[0],
                    'time': row[1],
                    'type': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                })
            
            conn.close()
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching recent updates: {e}")
            return []
    
    def _get_event_status(self, event_id):
        """Get current event status and statistics"""
        try:
            import sqlite3
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT event_name, status, event_type, created_at, last_updated,
                       (SELECT COUNT(*) FROM live_event_updates WHERE event_id = ?) as update_count
                FROM live_events WHERE id = ?
            ''', (event_id, event_id))
            
            event_data = cursor.fetchone()
            if not event_data:
                return {'error': 'Event not found'}
            
            conn.close()
            
            return {
                'event_id': event_id,
                'name': event_data[0],
                'status': event_data[1],
                'type': event_data[2],
                'created_at': event_data[3],
                'last_updated': event_data[4],
                'update_count': event_data[5],
                'active_viewers': len(self.event_rooms.get(event_id, [])),
                'is_live': event_data[1] == 'live'
            }
            
        except Exception as e:
            logger.error(f"Error getting event status: {e}")
            return {'error': 'Unable to fetch event status'}
    
    def get_performance_metrics(self):
        """Get current performance metrics"""
        return {
            **self.performance_metrics,
            'total_active_events': len([rooms for rooms in self.event_rooms.values() if rooms]),
            'total_subscribed_users': len(self.user_subscriptions),
            'timestamp': datetime.now().isoformat()
        }

# Event categorization and priority system
class EventPriorityManager:
    
    PRIORITY_LEVELS = {
        'critical': 1,    # Breaking news, major sports moments
        'high': 2,        # Important updates, goals, significant events
        'normal': 3,      # Regular updates
        'low': 4          # Background information, statistics
    }
    
    EVENT_CATEGORIES = {
        'sports': {
            'goal': 'critical',
            'red_card': 'high',
            'yellow_card': 'normal',
            'substitution': 'low',
            'corner': 'low',
            'penalty': 'critical'
        },
        'financial': {
            'market_crash': 'critical',
            'major_announcement': 'high',
            'earnings_report': 'normal',
            'price_update': 'low'
        },
        'politics': {
            'breaking_news': 'critical',
            'policy_announcement': 'high',
            'speech': 'normal',
            'meeting': 'low'
        }
    }
    
    @classmethod
    def get_priority(cls, event_type, category, update_type):
        """Determine priority level for an event update"""
        if category in cls.EVENT_CATEGORIES:
            if update_type in cls.EVENT_CATEGORIES[category]:
                priority = cls.EVENT_CATEGORIES[category][update_type]
                return cls.PRIORITY_LEVELS[priority]
        
        return cls.PRIORITY_LEVELS['normal']

# Enhanced notification system
class LiveEventNotificationManager:
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.notification_queue = queue.Queue()
        self._start_notification_processor()
    
    def _start_notification_processor(self):
        """Start background notification processor"""
        def process_notifications():
            while True:
                try:
                    if not self.notification_queue.empty():
                        notification = self.notification_queue.get(timeout=1)
                        self._send_notification(notification)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
        
        threading.Thread(target=process_notifications, daemon=True).start()
    
    def queue_notification(self, user_id, event_id, notification_data):
        """Queue a notification for a user"""
        notification = {
            'user_id': user_id,
            'event_id': event_id,
            'data': notification_data,
            'timestamp': datetime.now().isoformat(),
            'priority': notification_data.get('priority', 'normal')
        }
        
        self.notification_queue.put(notification)
    
    def _send_notification(self, notification):
        """Send notification to specific user"""
        user_room = f"user_{notification['user_id']}"
        
        notification_data = {
            'type': 'live_event_notification',
            'event_id': notification['event_id'],
            'message': notification['data'],
            'timestamp': notification['timestamp'],
            'priority': notification['priority']
        }
        
        self.socketio.emit('notification', notification_data, room=user_room)
    
    def get_active_events(self):
        """Get all currently active live events"""
        try:
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, event_name, event_type, category, status, start_time, 
                       end_time, venue, description, last_updated
                FROM live_events 
                WHERE status IN ('live', 'upcoming')
                ORDER BY start_time ASC
            ''')
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'category': row[3],
                    'status': row[4],
                    'start_time': row[5],
                    'end_time': row[6],
                    'venue': row[7],
                    'description': row[8],
                    'last_updated': row[9]
                })
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error fetching active events: {e}")
            return []
    
    def get_event_status(self, event_id):
        """Get current status of a specific event"""
        try:
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, event_name, status, start_time, end_time, last_updated
                FROM live_events 
                WHERE id = ?
            ''', (event_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'status': result[2],
                    'start_time': result[3],
                    'end_time': result[4],
                    'last_updated': result[5]
                }
            else:
                return {'error': 'Event not found'}
                
        except Exception as e:
            logger.error(f"Error fetching event status for {event_id}: {e}")
            return {'error': 'Database error'}
