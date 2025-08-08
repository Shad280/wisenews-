"""
Database Lock Fix and Optimization Script
Fixes existing database locks and optimizes the database for better performance
"""

import sqlite3
import logging
import os
import time
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

def fix_database_locks():
    """Fix database locks and optimize database"""
    
    db_path = 'news_database.db'
    backup_path = f'news_database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    try:
        # 1. Create backup first
        print("Creating database backup...")
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"Backup created: {backup_path}")
        
        # 2. Close any existing connections (if possible)
        print("Attempting to close existing connections...")
        
        # 3. Force unlock by opening with short timeout and using WAL mode
        print("Fixing database locks...")
        
        # First, try to enable WAL mode which allows better concurrency
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=5.0)
            
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('PRAGMA busy_timeout=30000')
            
            # Run VACUUM to optimize database
            print("Optimizing database structure...")
            conn.execute('VACUUM')
            
            # Analyze tables for better query performance
            print("Analyzing database for query optimization...")
            conn.execute('ANALYZE')
            
            conn.commit()
            print("Database optimization completed successfully!")
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("Database is still locked. Attempting emergency recovery...")
                
                # Emergency recovery: recreate database if critically locked
                if conn:
                    conn.close()
                
                # Wait a moment
                time.sleep(2)
                
                # Try to delete WAL and SHM files
                wal_file = db_path + '-wal'
                shm_file = db_path + '-shm'
                
                for file in [wal_file, shm_file]:
                    if os.path.exists(file):
                        try:
                            os.remove(file)
                            print(f"Removed {file}")
                        except:
                            print(f"Could not remove {file}")
                
                # Try again
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA busy_timeout=30000')
                conn.commit()
                print("Emergency recovery completed!")
            else:
                raise
        
        finally:
            if conn:
                conn.close()
        
        # 4. Verify database integrity
        print("Verifying database integrity...")
        conn = sqlite3.connect(db_path, timeout=10.0)
        try:
            result = conn.execute('PRAGMA integrity_check').fetchone()
            if result[0] == 'ok':
                print("Database integrity check: PASSED")
            else:
                print(f"Database integrity check: FAILED - {result[0]}")
        finally:
            conn.close()
        
        print("Database lock fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing database locks: {e}")
        logger.error(f"Database lock fix failed: {e}")
        
        # If backup exists, suggest restoration
        if os.path.exists(backup_path):
            print(f"Backup available at: {backup_path}")
            print("You may need to restore from backup if issues persist.")
        
        return False

def optimize_database_settings():
    """Apply optimal database settings"""
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        
        # Apply optimal settings
        settings = [
            'PRAGMA journal_mode=WAL',
            'PRAGMA synchronous=NORMAL', 
            'PRAGMA cache_size=10000',
            'PRAGMA temp_store=MEMORY',
            'PRAGMA mmap_size=268435456',  # 256MB
            'PRAGMA busy_timeout=30000',
            'PRAGMA wal_autocheckpoint=1000'
        ]
        
        for setting in settings:
            conn.execute(setting)
            
        conn.commit()
        conn.close()
        
        print("Database settings optimized!")
        return True
        
    except Exception as e:
        print(f"Error optimizing database settings: {e}")
        return False

if __name__ == "__main__":
    print("Starting database lock fix and optimization...")
    
    # Step 1: Fix locks
    if fix_database_locks():
        print("✅ Database locks fixed successfully")
    else:
        print("❌ Failed to fix database locks")
    
    # Step 2: Optimize settings
    if optimize_database_settings():
        print("✅ Database settings optimized")
    else:
        print("❌ Failed to optimize database settings")
    
    print("Database maintenance completed!")
