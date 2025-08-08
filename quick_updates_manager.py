"""
Quick Updates Manager for WiseNews
Optimized for ultra-fast news updates and real-time performance
"""

import sqlite3
import threading
import time
import json
import queue
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuickUpdatesManager:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.update_queue = queue.Queue()
        self.batch_queue = queue.Queue()
        
        # In-memory caches for speed
        self.article_cache = {}  # article_id -> article_data
        self.category_cache = {}  # category -> article_ids
        self.source_cache = {}   # source -> article_ids
        self.search_cache = {}   # query -> results (with TTL)
        
        # Performance metrics
        self.metrics = {
            'total_updates': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_update_time': 0,
            'last_update': None
        }
        
        # Update subscribers
        self.subscribers = defaultdict(set)  # event_type -> set of session_ids
        
        # Start background processors
        self._start_processors()
        
        logger.info("Quick Updates Manager initialized")
    
    def _start_processors(self):
        """Start background processing threads"""
        
        # Individual update processor
        def process_updates():
            while True:
                try:
                    update = self.update_queue.get(timeout=1)
                    start_time = time.time()
                    
                    self._process_single_update(update)
                    
                    # Update metrics
                    process_time = time.time() - start_time
                    self.metrics['total_updates'] += 1
                    self.metrics['avg_update_time'] = (
                        (self.metrics['avg_update_time'] * (self.metrics['total_updates'] - 1) + process_time) 
                        / self.metrics['total_updates']
                    )
                    self.metrics['last_update'] = datetime.now().isoformat()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing update: {e}")
        
        # Batch update processor
        def process_batch_updates():
            batch = []
            last_batch_time = time.time()
            
            while True:
                try:
                    # Collect updates for 100ms or until we have 10 items
                    current_time = time.time()
                    
                    if current_time - last_batch_time >= 0.1 or len(batch) >= 10:
                        if batch:
                            self._process_batch_updates(batch)
                            batch = []
                            last_batch_time = current_time
                    
                    try:
                        update = self.batch_queue.get(timeout=0.05)
                        batch.append(update)
                    except queue.Empty:
                        continue
                        
                except Exception as e:
                    logger.error(f"Error in batch processing: {e}")
                    time.sleep(0.1)
        
        # Cache cleanup processor
        def cleanup_cache():
            while True:
                try:
                    time.sleep(300)  # Clean every 5 minutes
                    self._cleanup_expired_cache()
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
        
        # Start all processors
        threading.Thread(target=process_updates, daemon=True).start()
        threading.Thread(target=process_batch_updates, daemon=True).start()
        threading.Thread(target=cleanup_cache, daemon=True).start()
        
        logger.info("Quick update processors started")
    
    def add_quick_update(self, update_type: str, data: Dict[str, Any], priority: str = 'normal'):
        """Add an update to the quick processing queue"""
        update = {
            'type': update_type,
            'data': data,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'id': f"{update_type}_{int(time.time() * 1000)}"
        }
        
        if priority == 'high':
            # High priority updates go to individual queue for immediate processing
            self.update_queue.put(update)
        else:
            # Normal updates can be batched
            self.batch_queue.put(update)
    
    def _process_single_update(self, update: Dict[str, Any]):
        """Process a single high-priority update immediately"""
        update_type = update['type']
        data = update['data']
        
        try:
            if update_type == 'new_article':
                self._handle_new_article(data)
            elif update_type == 'article_update':
                self._handle_article_update(data)
            elif update_type == 'live_event_update':
                self._handle_live_event_update(data)
            elif update_type == 'category_update':
                self._handle_category_update(data)
            elif update_type == 'cache_invalidation':
                self._handle_cache_invalidation(data)
            
            # Broadcast to WebSocket subscribers
            if self.socketio:
                self._broadcast_update(update)
                
        except Exception as e:
            logger.error(f"Error processing update {update_type}: {e}")
    
    def _process_batch_updates(self, updates: List[Dict[str, Any]]):
        """Process multiple updates in a single database transaction"""
        if not updates:
            return
        
        try:
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            # Group updates by type for efficient processing
            grouped_updates = defaultdict(list)
            for update in updates:
                grouped_updates[update['type']].append(update)
            
            # Process each type in batches
            for update_type, type_updates in grouped_updates.items():
                if update_type == 'new_article':
                    self._batch_insert_articles(cursor, type_updates)
                elif update_type == 'article_update':
                    self._batch_update_articles(cursor, type_updates)
                elif update_type == 'view_count':
                    self._batch_update_view_counts(cursor, type_updates)
            
            conn.commit()
            conn.close()
            
            # Update caches and broadcast
            for update in updates:
                self._update_cache_for_update(update)
                if self.socketio:
                    self._broadcast_update(update)
                    
            logger.info(f"Processed batch of {len(updates)} updates")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
    
    def _handle_new_article(self, data: Dict[str, Any]):
        """Handle new article with optimized caching"""
        article_id = data.get('id')
        if not article_id:
            return
        
        # Add to cache immediately
        self.article_cache[article_id] = data
        
        # Update category cache
        category = data.get('category')
        if category:
            if category not in self.category_cache:
                self.category_cache[category] = set()
            self.category_cache[category].add(article_id)
        
        # Update source cache
        source = data.get('source_name')
        if source:
            if source not in self.source_cache:
                self.source_cache[source] = set()
            self.source_cache[source].add(article_id)
        
        # Invalidate search cache (new content available)
        self.search_cache.clear()
    
    def _handle_article_update(self, data: Dict[str, Any]):
        """Handle article updates efficiently"""
        article_id = data.get('id')
        if not article_id:
            return
        
        # Update cache
        if article_id in self.article_cache:
            self.article_cache[article_id].update(data)
        
        # If category changed, update category cache
        if 'category' in data:
            # Remove from old category
            old_article = self.article_cache.get(article_id, {})
            old_category = old_article.get('category')
            if old_category and old_category in self.category_cache:
                self.category_cache[old_category].discard(article_id)
            
            # Add to new category
            new_category = data['category']
            if new_category not in self.category_cache:
                self.category_cache[new_category] = set()
            self.category_cache[new_category].add(article_id)
    
    def _handle_live_event_update(self, data: Dict[str, Any]):
        """Handle live event updates with priority broadcasting"""
        event_id = data.get('event_id')
        if not event_id:
            return
        
        # High-priority broadcast for live events
        if self.socketio:
            self.socketio.emit('live_event_update', {
                'event_id': event_id,
                'update': data,
                'timestamp': datetime.now().isoformat()
            }, room=f'event_{event_id}')
    
    def _broadcast_update(self, update: Dict[str, Any]):
        """Broadcast update to WebSocket subscribers"""
        if not self.socketio:
            return
        
        update_type = update['type']
        
        # Broadcast to general subscribers
        self.socketio.emit('quick_update', {
            'type': update_type,
            'data': update['data'],
            'timestamp': update['timestamp']
        }, room='quick_updates')
        
        # Broadcast to type-specific subscribers
        if update_type in self.subscribers:
            self.socketio.emit(f'{update_type}_update', update, 
                             room=f'{update_type}_subscribers')
    
    def subscribe_to_updates(self, session_id: str, update_types: List[str]):
        """Subscribe a WebSocket session to specific update types"""
        for update_type in update_types:
            self.subscribers[update_type].add(session_id)
    
    def unsubscribe_from_updates(self, session_id: str, update_types: List[str] = None):
        """Unsubscribe from updates"""
        if update_types is None:
            # Unsubscribe from all
            for subscribers in self.subscribers.values():
                subscribers.discard(session_id)
        else:
            for update_type in update_types:
                self.subscribers[update_type].discard(session_id)
    
    def get_cached_articles(self, category: str = None, source: str = None, 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """Get articles from cache with filtering"""
        try:
            article_ids = set()
            
            if category and category in self.category_cache:
                article_ids = self.category_cache[category]
                self.metrics['cache_hits'] += 1
            elif source and source in self.source_cache:
                article_ids = self.source_cache[source]
                self.metrics['cache_hits'] += 1
            else:
                # Cache miss - need to query database
                self.metrics['cache_misses'] += 1
                return self._query_articles_from_db(category, source, limit)
            
            # Get articles from cache
            articles = []
            for article_id in list(article_ids)[:limit]:
                if article_id in self.article_cache:
                    articles.append(self.article_cache[article_id])
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting cached articles: {e}")
            return []
    
    def _query_articles_from_db(self, category: str = None, source: str = None, 
                               limit: int = 20) -> List[Dict[str, Any]]:
        """Fallback database query when cache miss occurs"""
        try:
            conn = sqlite3.connect('news_database.db', check_same_thread=False)
            cursor = conn.cursor()
            
            where_conditions = ['is_deleted = 0']
            params = []
            
            if category:
                where_conditions.append('category = ?')
                params.append(category)
            
            if source:
                where_conditions.append('source_name = ?')
                params.append(source)
            
            where_clause = 'WHERE ' + ' AND '.join(where_conditions)
            
            cursor.execute(f'''
                SELECT id, title, content, source_type, source_name, category, 
                       date_added, keywords, read_status
                FROM articles 
                {where_clause}
                ORDER BY date_added DESC 
                LIMIT ?
            ''', params + [limit])
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'source_type': row[3],
                    'source_name': row[4],
                    'category': row[5],
                    'date_added': row[6],
                    'keywords': row[7],
                    'read_status': row[8]
                }
                articles.append(article)
                
                # Update cache while we're here
                self.article_cache[article['id']] = article
                
                if category:
                    if category not in self.category_cache:
                        self.category_cache[category] = set()
                    self.category_cache[category].add(article['id'])
                
                if source:
                    if source not in self.source_cache:
                        self.source_cache[source] = set()
                    self.source_cache[source].add(article['id'])
            
            conn.close()
            return articles
            
        except Exception as e:
            logger.error(f"Error querying articles from database: {e}")
            return []
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            # Clear search cache (it has TTL)
            current_time = time.time()
            expired_keys = []
            
            for key, value in self.search_cache.items():
                if isinstance(value, dict) and 'timestamp' in value:
                    if current_time - value['timestamp'] > 300:  # 5 minutes TTL
                        expired_keys.append(key)
            
            for key in expired_keys:
                del self.search_cache[key]
            
            # Limit cache sizes to prevent memory issues
            if len(self.article_cache) > 1000:
                # Keep only the most recent 800 articles
                sorted_articles = sorted(self.article_cache.items(), 
                                       key=lambda x: x[1].get('date_added', ''), 
                                       reverse=True)
                self.article_cache = dict(sorted_articles[:800])
            
            logger.info(f"Cache cleanup completed. Articles: {len(self.article_cache)}, "
                       f"Categories: {len(self.category_cache)}, Sources: {len(self.source_cache)}")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        cache_hit_rate = 0
        total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_requests > 0:
            cache_hit_rate = (self.metrics['cache_hits'] / total_requests) * 100
        
        return {
            'total_updates': self.metrics['total_updates'],
            'avg_update_time_ms': round(self.metrics['avg_update_time'] * 1000, 2),
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'cached_articles': len(self.article_cache),
            'cached_categories': len(self.category_cache),
            'cached_sources': len(self.source_cache),
            'active_subscribers': sum(len(subs) for subs in self.subscribers.values()),
            'last_update': self.metrics['last_update'],
            'queue_sizes': {
                'individual': self.update_queue.qsize(),
                'batch': self.batch_queue.qsize()
            }
        }

# Global instance
quick_updates_manager = None

def get_quick_updates_manager(socketio=None):
    """Get or create the global quick updates manager"""
    global quick_updates_manager
    if quick_updates_manager is None:
        quick_updates_manager = QuickUpdatesManager(socketio)
    return quick_updates_manager
