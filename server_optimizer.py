"""
WiseNews Server Optimization Script
Optimizes the Flask application for production use on current hardware
"""

import os
import sys
import sqlite3
import threading
import time
import gc
import psutil
from datetime import datetime, timedelta
import logging
from functools import wraps
import json

class ServerOptimizer:
    def __init__(self):
        self.db_path = 'news_database.db'
        self.cache = {}
        self.cache_ttl = {}
        self.max_cache_size = 1000
        self.db_pool = []
        self.db_pool_size = 5
        self.memory_threshold = 85  # Percentage
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('logs/optimization.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def init_database_pool(self):
        """Initialize database connection pool"""
        try:
            for _ in range(self.db_pool_size):
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30,
                    check_same_thread=False,
                    isolation_level=None  # Autocommit mode
                )
                
                # SQLite optimizations
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                conn.execute("PRAGMA page_size=4096")
                
                self.db_pool.append(conn)
                
            self.logger.info(f"Database pool initialized with {len(self.db_pool)} connections")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            
    def get_db_connection(self):
        """Get database connection from pool"""
        if self.db_pool:
            return self.db_pool.pop()
        else:
            # Fallback: create new connection
            conn = sqlite3.connect(self.db_path, timeout=30)
            self.optimize_sqlite_connection(conn)
            return conn
            
    def return_db_connection(self, conn):
        """Return database connection to pool"""
        if len(self.db_pool) < self.db_pool_size:
            self.db_pool.append(conn)
        else:
            conn.close()
            
    def optimize_sqlite_connection(self, conn):
        """Apply SQLite optimizations to connection"""
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA mmap_size=268435456")
            conn.execute("PRAGMA page_size=4096")
            conn.execute("PRAGMA optimize")
        except Exception as e:
            self.logger.error(f"Failed to optimize SQLite connection: {e}")
            
    def memory_cache_decorator(self, ttl=300):
        """Memory caching decorator with TTL"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Check if cached and not expired
                now = time.time()
                if (cache_key in self.cache and 
                    cache_key in self.cache_ttl and 
                    now < self.cache_ttl[cache_key]):
                    return self.cache[cache_key]
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                
                # Manage cache size
                if len(self.cache) >= self.max_cache_size:
                    # Remove oldest entries
                    oldest_keys = sorted(
                        self.cache_ttl.keys(),
                        key=lambda k: self.cache_ttl[k]
                    )[:100]
                    for key in oldest_keys:
                        self.cache.pop(key, None)
                        self.cache_ttl.pop(key, None)
                
                # Cache the result
                self.cache[cache_key] = result
                self.cache_ttl[cache_key] = now + ttl
                
                return result
            return wrapper
        return decorator
        
    def optimize_database_structure(self):
        """Optimize database structure and indexes"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date)",
                "CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)",
                "CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)",
                "CREATE INDEX IF NOT EXISTS idx_articles_deleted ON articles(is_deleted)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_user_usage_date ON user_daily_usage(date)",
                "CREATE INDEX IF NOT EXISTS idx_user_usage_user ON user_daily_usage(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_article_images_article ON article_images(article_id)",
                "CREATE INDEX IF NOT EXISTS idx_live_events_created ON live_events(created_at)"
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    self.logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    if "already exists" not in str(e):
                        self.logger.error(f"Failed to create index: {e}")
            
            # Optimize database
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.execute("REINDEX")
            
            conn.commit()
            self.return_db_connection(conn)
            
            self.logger.info("Database structure optimization completed")
            
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            
    def cleanup_old_data(self):
        """Clean up old data to improve performance"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Delete articles older than 90 days
            ninety_days_ago = datetime.now() - timedelta(days=90)
            cursor.execute(
                "DELETE FROM articles WHERE published_date < ? AND is_deleted = 1",
                (ninety_days_ago.isoformat(),)
            )
            deleted_articles = cursor.rowcount
            
            # Delete old user usage data (keep last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute(
                "DELETE FROM user_daily_usage WHERE date < ?",
                (thirty_days_ago.strftime('%Y-%m-%d'),)
            )
            deleted_usage = cursor.rowcount
            
            # Delete orphaned images
            cursor.execute("""
                DELETE FROM article_images 
                WHERE article_id NOT IN (SELECT id FROM articles)
            """)
            deleted_images = cursor.rowcount
            
            # Delete old live events (keep last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            cursor.execute(
                "DELETE FROM live_events WHERE created_at < ?",
                (seven_days_ago.isoformat(),)
            )
            deleted_events = cursor.rowcount
            
            conn.commit()
            self.return_db_connection(conn)
            
            self.logger.info(f"Cleanup completed: {deleted_articles} articles, "
                           f"{deleted_usage} usage records, {deleted_images} images, "
                           f"{deleted_events} events deleted")
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
            
    def monitor_memory_usage(self):
        """Monitor and manage memory usage"""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            memory_info = process.memory_info()
            
            if memory_percent > self.memory_threshold:
                self.logger.warning(f"High memory usage: {memory_percent:.1f}%")
                
                # Force garbage collection
                gc.collect()
                
                # Clear cache if memory is critically high
                if memory_percent > 90:
                    self.cache.clear()
                    self.cache_ttl.clear()
                    self.logger.info("Emergency cache clear due to high memory usage")
                    
            return {
                'memory_percent': memory_percent,
                'memory_mb': memory_info.rss / 1024 / 1024,
                'cache_size': len(self.cache)
            }
            
        except Exception as e:
            self.logger.error(f"Memory monitoring failed: {e}")
            return None
            
    def optimize_static_files(self):
        """Optimize static file serving"""
        try:
            static_dir = 'static'
            if not os.path.exists(static_dir):
                return
                
            # Get file statistics
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                        
            self.logger.info(f"Static files: {file_count} files, "
                           f"{total_size / 1024 / 1024:.1f} MB total")
            
        except Exception as e:
            self.logger.error(f"Static file optimization failed: {e}")
            
    def create_optimization_report(self):
        """Create comprehensive optimization report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / 1024**3,
                    'memory_available_gb': psutil.virtual_memory().available / 1024**3,
                    'disk_usage_gb': psutil.disk_usage('.').used / 1024**3
                },
                'database_info': {},
                'cache_info': {
                    'cache_size': len(self.cache),
                    'max_cache_size': self.max_cache_size
                },
                'recommendations': []
            }
            
            # Database statistics
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count records in main tables
            tables = ['articles', 'users', 'user_subscriptions', 'user_daily_usage', 'live_events']
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    report['database_info'][f'{table}_count'] = count
                except:
                    report['database_info'][f'{table}_count'] = 0
                    
            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_mb = (page_count * page_size) / 1024 / 1024
            report['database_info']['size_mb'] = db_size_mb
            
            self.return_db_connection(conn)
            
            # Generate recommendations
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 80:
                report['recommendations'].append("Consider increasing system RAM or optimizing memory usage")
                
            if db_size_mb > 500:
                report['recommendations'].append("Database is large - consider archiving old data")
                
            if len(self.cache) > self.max_cache_size * 0.8:
                report['recommendations'].append("Cache is near capacity - consider increasing cache size")
                
            # Save report
            os.makedirs('logs', exist_ok=True)
            with open('logs/optimization_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info("Optimization report created")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to create optimization report: {e}")
            return None
            
    def start_background_optimization(self):
        """Start background optimization tasks"""
        def optimization_worker():
            while True:
                try:
                    # Run optimizations every hour
                    time.sleep(3600)
                    
                    # Monitor memory
                    self.monitor_memory_usage()
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Clean cache if it's getting too large
                    if len(self.cache) > self.max_cache_size * 0.9:
                        # Remove expired entries
                        now = time.time()
                        expired_keys = [
                            key for key, ttl in self.cache_ttl.items()
                            if now > ttl
                        ]
                        for key in expired_keys:
                            self.cache.pop(key, None)
                            self.cache_ttl.pop(key, None)
                            
                    self.logger.info("Background optimization cycle completed")
                    
                except Exception as e:
                    self.logger.error(f"Background optimization error: {e}")
                    
        # Start background thread
        thread = threading.Thread(target=optimization_worker, daemon=True)
        thread.start()
        self.logger.info("Background optimization started")
        
    def run_full_optimization(self):
        """Run complete server optimization"""
        self.logger.info("Starting full server optimization...")
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize database pool
        self.init_database_pool()
        
        # Optimize database
        self.optimize_database_structure()
        
        # Clean old data
        self.cleanup_old_data()
        
        # Optimize static files
        self.optimize_static_files()
        
        # Start background optimization
        self.start_background_optimization()
        
        # Create optimization report
        report = self.create_optimization_report()
        
        self.logger.info("Server optimization completed successfully!")
        return report

# Global optimizer instance
optimizer = ServerOptimizer()

# Decorator for caching database queries
def cache_db_query(ttl=300):
    return optimizer.memory_cache_decorator(ttl)

# Function to get optimized database connection
def get_optimized_db_connection():
    return optimizer.get_db_connection()

def return_optimized_db_connection(conn):
    return optimizer.return_db_connection(conn)

if __name__ == "__main__":
    # Run optimization when script is executed directly
    optimizer.run_full_optimization()
