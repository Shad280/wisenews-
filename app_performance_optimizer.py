"""
Advanced Application Performance Optimizer
Implements gzip compression, response caching, and application-level optimizations
"""

from flask import Flask, request, make_response, g
import gzip
import functools
import time
import json
from io import BytesIO
import sqlite3
import threading
from datetime import datetime, timedelta

class ApplicationOptimizer:
    def __init__(self, app):
        self.app = app
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = 300  # 5 minutes default TTL
        
    def enable_gzip_compression(self):
        """Enable gzip compression for all responses"""
        
        @self.app.after_request
        def compress_response(response):
            # Only compress if response is large enough and client accepts gzip
            if (response.content_length and response.content_length > 1024 and
                'gzip' in request.headers.get('Accept-Encoding', '')):
                
                # Don't compress already compressed content
                if response.headers.get('Content-Encoding'):
                    return response
                
                # Compress the response data
                gzip_buffer = BytesIO()
                with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as gzip_file:
                    gzip_file.write(response.get_data())
                
                response.set_data(gzip_buffer.getvalue())
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(response.get_data())
                
            return response
    
    def add_cache_headers(self):
        """Add appropriate cache headers to responses"""
        
        @self.app.after_request
        def add_cache_headers(response):
            # Static assets - cache for 1 day
            if request.endpoint and 'static' in request.endpoint:
                response.headers['Cache-Control'] = 'public, max-age=86400'
            
            # API responses - cache for 5 minutes
            elif request.endpoint and 'api' in request.endpoint:
                response.headers['Cache-Control'] = 'public, max-age=300'
            
            # HTML pages - cache for 1 minute
            else:
                response.headers['Cache-Control'] = 'public, max-age=60'
            
            return response
    
    def cached_query(self, cache_key, query_func, ttl=None):
        """Cache database query results"""
        if ttl is None:
            ttl = self.cache_ttl
        
        with self.cache_lock:
            # Check if cached result exists and is still valid
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < ttl:
                    return cached_data
            
            # Execute query and cache result
            result = query_func()
            self.cache[cache_key] = (result, time.time())
            
            # Clean old cache entries periodically
            if len(self.cache) > 1000:
                self._clean_cache()
            
            return result
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, (data, timestamp) in self.cache.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def optimize_database_connections(self):
        """Optimize database connection handling"""
        
        def get_db():
            """Get database connection with optimized settings"""
            if 'db' not in g:
                g.db = sqlite3.connect(
                    'news_database.db',
                    check_same_thread=False,
                    timeout=20.0
                )
                g.db.row_factory = sqlite3.Row
                
                # Apply performance optimizations
                cursor = g.db.cursor()
                cursor.execute('PRAGMA cache_size = -65536')  # 64MB cache
                cursor.execute('PRAGMA journal_mode = WAL')
                cursor.execute('PRAGMA synchronous = NORMAL')
                cursor.execute('PRAGMA temp_store = MEMORY')
                cursor.execute('PRAGMA mmap_size = 268435456')  # 256MB mmap
                
            return g.db
        
        def close_db(error):
            """Close database connection"""
            db = g.pop('db', None)
            if db is not None:
                db.close()
        
        self.app.teardown_appcontext(close_db)
        return get_db
    
    def create_optimized_routes(self):
        """Create optimized versions of common routes"""
        
        get_db = self.optimize_database_connections()
        
        @self.app.route('/api/articles-fast')
        def get_articles_fast():
            """Optimized articles endpoint with caching"""
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            category = request.args.get('category', '')
            source = request.args.get('source', '')
            
            # Create cache key
            cache_key = f"articles_{page}_{per_page}_{category}_{source}"
            
            def fetch_articles():
                db = get_db()
                cursor = db.cursor()
                
                # Build optimized query
                where_conditions = []
                params = []
                
                if category:
                    where_conditions.append('category = ?')
                    params.append(category)
                
                if source:
                    where_conditions.append('source_name LIKE ?')
                    params.append(f'%{source}%')
                
                where_clause = ' AND '.join(where_conditions)
                if where_clause:
                    where_clause = 'WHERE ' + where_clause
                
                offset = (page - 1) * per_page
                
                # Use optimized query with proper indexes
                query = f'''
                    SELECT id, title, content, source_name, date_added, category
                    FROM articles 
                    {where_clause}
                    ORDER BY date_added DESC 
                    LIMIT ? OFFSET ?
                '''
                params.extend([per_page, offset])
                
                cursor.execute(query, params)
                articles = [dict(row) for row in cursor.fetchall()]
                
                # Get total count for pagination
                count_query = f'SELECT COUNT(*) FROM articles {where_clause}'
                cursor.execute(count_query, params[:-2])  # Exclude LIMIT/OFFSET params
                total = cursor.fetchone()[0]
                
                return {
                    'articles': articles,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'has_more': offset + per_page < total
                }
            
            # Use cached result
            result = self.cached_query(cache_key, fetch_articles, ttl=60)  # 1 minute cache
            return json.dumps(result, default=str)
        
        @self.app.route('/api/stats-fast')
        def get_stats_fast():
            """Optimized stats endpoint with caching"""
            
            def fetch_stats():
                db = get_db()
                cursor = db.cursor()
                
                # Use optimized queries with proper indexes
                cursor.execute('SELECT COUNT(*) FROM articles')
                total_articles = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT source_name) FROM articles')
                total_sources = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT category) FROM articles')
                total_categories = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM articles 
                    WHERE date_added >= date('now', '-1 day')
                ''')
                articles_today = cursor.fetchone()[0]
                
                return {
                    'total_articles': total_articles,
                    'total_sources': total_sources,
                    'total_categories': total_categories,
                    'articles_today': articles_today,
                    'last_updated': datetime.now().isoformat()
                }
            
            result = self.cached_query('app_stats', fetch_stats, ttl=300)  # 5 minute cache
            return json.dumps(result, default=str)
    
    def add_performance_headers(self):
        """Add performance monitoring headers"""
        
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                response_time = (time.time() - g.start_time) * 1000
                response.headers['X-Response-Time'] = f'{response_time:.2f}ms'
            return response
    
    def apply_all_optimizations(self):
        """Apply all performance optimizations"""
        print("🚀 Applying performance optimizations...")
        
        self.enable_gzip_compression()
        print("✅ Gzip compression enabled")
        
        self.add_cache_headers()
        print("✅ Cache headers configured")
        
        self.create_optimized_routes()
        print("✅ Optimized routes created")
        
        self.add_performance_headers()
        print("✅ Performance monitoring headers added")
        
        print("🎉 All optimizations applied successfully!")

def optimize_app(app):
    """Apply all optimizations to a Flask app"""
    optimizer = ApplicationOptimizer(app)
    optimizer.apply_all_optimizations()
    return optimizer
