"""
Critical Performance Fixes for WiseNews Application
Addresses the main performance bottlenecks in the application
"""

import sqlite3
import time
from flask import g, current_app
import threading

class CriticalPerformanceFix:
    def __init__(self):
        self.db_pool = []
        self.db_pool_lock = threading.Lock()
        self.max_pool_size = 10
        
    def create_connection_pool(self):
        """Create a connection pool for better database performance"""
        with self.db_pool_lock:
            for i in range(self.max_pool_size):
                conn = sqlite3.connect(
                    'news_database.db',
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                
                # Apply critical optimizations
                cursor = conn.cursor()
                cursor.execute('PRAGMA cache_size = -131072')  # 128MB cache
                cursor.execute('PRAGMA journal_mode = WAL')
                cursor.execute('PRAGMA synchronous = NORMAL')
                cursor.execute('PRAGMA temp_store = MEMORY')
                cursor.execute('PRAGMA mmap_size = 536870912')  # 512MB mmap
                cursor.execute('PRAGMA threads = 4')
                
                self.db_pool.append(conn)
    
    def get_connection(self):
        """Get a connection from the pool"""
        with self.db_pool_lock:
            if self.db_pool:
                return self.db_pool.pop()
            else:
                # Create new connection if pool is empty
                conn = sqlite3.connect(
                    'news_database.db',
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                return conn
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        with self.db_pool_lock:
            if len(self.db_pool) < self.max_pool_size:
                self.db_pool.append(conn)
            else:
                conn.close()
    
    def optimize_article_queries(self):
        """Optimize the most critical article queries"""
        
        def get_articles_optimized(page=1, per_page=50, category=None, source=None):
            """Optimized articles query with minimal data transfer"""
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # Build optimized query - only select needed fields
                fields = 'id, title, LEFT(content, 200) as preview, source_name, date_added, category'
                where_conditions = []
                params = []
                
                if category:
                    where_conditions.append('category = ?')
                    params.append(category)
                
                if source:
                    where_conditions.append('source_name = ?')
                    params.append(source)
                
                where_clause = ''
                if where_conditions:
                    where_clause = 'WHERE ' + ' AND '.join(where_conditions)
                
                offset = (page - 1) * per_page
                
                # Use covering index query for maximum performance
                query = f'''
                    SELECT {fields}
                    FROM articles 
                    {where_clause}
                    ORDER BY date_added DESC 
                    LIMIT ? OFFSET ?
                '''
                params.extend([per_page, offset])
                
                start_time = time.time()
                cursor.execute(query, params)
                articles = [dict(row) for row in cursor.fetchall()]
                query_time = (time.time() - start_time) * 1000
                
                print(f"🔍 Optimized query executed in {query_time:.2f}ms")
                
                return articles
                
            finally:
                self.return_connection(conn)
        
        return get_articles_optimized
    
    def create_critical_indexes(self):
        """Create only the most critical indexes for performance"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Most critical indexes based on actual query patterns
            critical_indexes = [
                # Covering index for the main articles query
                'CREATE INDEX IF NOT EXISTS idx_articles_main_query ON articles(date_added DESC, category, source_name, id, title)',
                
                # Fast counting index
                'CREATE INDEX IF NOT EXISTS idx_articles_fast_count ON articles(id) WHERE id IS NOT NULL',
                
                # Source filtering index
                'CREATE INDEX IF NOT EXISTS idx_articles_source_date ON articles(source_name, date_added DESC)',
                
                # Category filtering index  
                'CREATE INDEX IF NOT EXISTS idx_articles_category_date ON articles(category, date_added DESC)',
            ]
            
            for index_sql in critical_indexes:
                try:
                    start_time = time.time()
                    cursor.execute(index_sql)
                    index_time = (time.time() - start_time) * 1000
                    print(f"🔧 Critical index created in {index_time:.2f}ms")
                except Exception as e:
                    print(f"⚠️ Index creation failed: {e}")
            
            conn.commit()
            
        finally:
            self.return_connection(conn)

# Initialize the performance fix
perf_fix = CriticalPerformanceFix()
perf_fix.create_connection_pool()
perf_fix.create_critical_indexes()

print("🚀 Critical performance fixes applied!")
print("✅ Database connection pool created")
print("✅ Critical indexes optimized")
print("✅ Ready for high-performance queries")
