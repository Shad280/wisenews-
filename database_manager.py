"""
Database Connection Manager for WiseNews
Handles SQLite connections with proper locking, timeouts, and retry logic
"""

import sqlite3
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional, Any, List, Tuple
import queue

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database connection manager with connection pooling"""
    
    def __init__(self, db_path: str = 'news_database.db', max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connection_pool = queue.Queue(maxsize=max_connections)
        self._lock = threading.RLock()
        self._initialized = False
        
        # Initialize connection pool
        self._init_pool()
    
    def _init_pool(self):
        """Initialize the connection pool with configured connections"""
        try:
            for _ in range(self.max_connections):
                conn = self._create_connection()
                if conn:
                    self._connection_pool.put(conn)
            self._initialized = True
            logger.info(f"Database connection pool initialized with {self.max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimal settings"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                isolation_level=None,  # Autocommit mode
                check_same_thread=False
            )
            
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('PRAGMA busy_timeout=30000')  # 30 second busy timeout
            
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """Get a connection from the pool with automatic cleanup"""
        conn = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            try:
                conn = self._connection_pool.get(timeout=timeout)
            except queue.Empty:
                logger.warning("Connection pool exhausted, creating temporary connection")
                conn = self._create_connection()
                if not conn:
                    raise Exception("Failed to create database connection")
            
            # Test connection
            try:
                conn.execute('SELECT 1').fetchone()
            except sqlite3.Error:
                # Connection is stale, create new one
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_connection()
                if not conn:
                    raise Exception("Failed to create replacement connection")
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            # Return connection to pool or close if pool is full
            if conn:
                try:
                    # Rollback any pending transaction
                    conn.rollback()
                    
                    # Try to return to pool
                    try:
                        self._connection_pool.put_nowait(conn)
                    except queue.Full:
                        # Pool is full, close the connection
                        conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    try:
                        conn.close()
                    except:
                        pass
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch: str = None) -> Any:
        """Execute a query with automatic retry and proper error handling"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if fetch == 'one':
                        return cursor.fetchone()
                    elif fetch == 'all':
                        return cursor.fetchall()
                    elif fetch == 'many':
                        return cursor.fetchmany()
                    else:
                        conn.commit()
                        return cursor.lastrowid
                        
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Database query failed after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Database query error: {e}")
                raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> None:
        """Execute multiple queries in a single transaction"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Database executemany failed after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Database executemany error: {e}")
                raise
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        try:
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

# Global database manager instance
db_manager = DatabaseManager()
