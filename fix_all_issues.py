#!/usr/bin/env python3
"""
Fix all identified database schema issues
"""

import sqlite3
from datetime import datetime

def fix_articles_table_schema():
    """Fix missing columns in articles table"""
    print("🔧 FIXING ARTICLES TABLE SCHEMA")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Check current articles table schema
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current articles columns: {columns}")
        
        # Add missing columns
        missing_columns = []
        
        if 'created_at' not in columns:
            cursor.execute('ALTER TABLE articles ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
            missing_columns.append('created_at')
            print("✅ Added created_at column")
        
        if 'published_date' not in columns:
            cursor.execute('ALTER TABLE articles ADD COLUMN published_date DATETIME')
            missing_columns.append('published_date')
            print("✅ Added published_date column")
        
        if 'source' not in columns:
            cursor.execute('ALTER TABLE articles ADD COLUMN source TEXT')
            missing_columns.append('source')
            print("✅ Added source column")
        
        # Update existing articles with timestamps if they don't have them
        if 'created_at' in missing_columns:
            cursor.execute("UPDATE articles SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            print("✅ Updated existing articles with timestamps")
        
        if 'published_date' in missing_columns:
            cursor.execute("UPDATE articles SET published_date = CURRENT_TIMESTAMP WHERE published_date IS NULL")
            print("✅ Updated existing articles with published dates")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Articles table schema fixed - Added {len(missing_columns)} columns")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix articles table: {e}")
        return False

def fix_user_daily_usage_table():
    """Create missing user_daily_usage table"""
    print("\n🔧 FIXING USER DAILY USAGE TABLE")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_daily_usage'")
        if not cursor.fetchone():
            # Create the table
            cursor.execute('''
                CREATE TABLE user_daily_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    articles_viewed INTEGER DEFAULT 0,
                    searches_performed INTEGER DEFAULT 0,
                    api_calls INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, date)
                )
            ''')
            print("✅ Created user_daily_usage table")
            
            # Create index
            cursor.execute('CREATE INDEX idx_user_daily_usage_user_date ON user_daily_usage(user_id, date)')
            print("✅ Created index for user_daily_usage")
        else:
            print("✅ user_daily_usage table already exists")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create user_daily_usage table: {e}")
        return False

def fix_user_auth_methods():
    """Fix user authentication methods"""
    print("\n🔧 FIXING USER AUTHENTICATION METHODS")
    print("=" * 50)
    
    try:
        # Read the user_auth.py file
        with open('user_auth.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if get_user_by_id method exists
        if 'def get_user_by_id(self' not in content:
            # Find the UserManager class and add the missing method
            import re
            
            # Find the end of the __init__ method
            pattern = r'(def __init__\(self.*?def\s+\w+)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                # Add the missing method before the next method
                insert_pos = match.end() - len(match.group(2).split('\n')[-1])
                
                missing_method = '''
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            conn = sqlite3.connect('news_database.db', timeout=30.0)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                columns = [description[0] for description in cursor.description]
                user_dict = dict(zip(columns, user_data))
                conn.close()
                return user_dict
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

'''
                
                new_content = content[:insert_pos] + missing_method + content[insert_pos:]
                
                with open('user_auth.py', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Added get_user_by_id method to UserManager")
            else:
                print("⚠️ Could not locate insertion point for get_user_by_id method")
        else:
            print("✅ get_user_by_id method already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix user auth methods: {e}")
        return False

def create_missing_indexes():
    """Create missing database indexes"""
    print("\n🔧 CREATING MISSING INDEXES")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # List of indexes to create (only for existing columns/tables)
        indexes = [
            ('idx_articles_category', 'CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)'),
            ('idx_articles_deleted', 'CREATE INDEX IF NOT EXISTS idx_articles_deleted ON articles(deleted)'),
            ('idx_users_email', 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'),
            ('idx_article_images_article', 'CREATE INDEX IF NOT EXISTS idx_article_images_article ON article_images(article_id)'),
            ('idx_live_events_created', 'CREATE INDEX IF NOT EXISTS idx_live_events_created ON live_events(created_at)'),
        ]
        
        # Check if columns exist before creating indexes
        cursor.execute("PRAGMA table_info(articles)")
        articles_columns = [col[1] for col in cursor.fetchall()]
        
        for index_name, index_sql in indexes:
            try:
                # Only create indexes for existing columns
                if 'articles' in index_sql:
                    if 'category' in index_sql and 'category' not in articles_columns:
                        print(f"⚠️ Skipping {index_name} - column 'category' doesn't exist")
                        continue
                    if 'deleted' in index_sql and 'deleted' not in articles_columns:
                        print(f"⚠️ Skipping {index_name} - column 'deleted' doesn't exist")
                        continue
                
                cursor.execute(index_sql)
                print(f"✅ Created index: {index_name}")
                
            except Exception as e:
                if "no such column" in str(e):
                    print(f"⚠️ Skipped {index_name} - column doesn't exist")
                else:
                    print(f"❌ Failed to create index {index_name}: {e}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")
        return False

def verify_fixes():
    """Verify all fixes are working"""
    print("\n🔍 VERIFYING ALL FIXES")
    print("=" * 50)
    
    issues = []
    
    try:
        conn = sqlite3.connect('news_database.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Test articles table with created_at
        try:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"✅ Articles with timestamps: {count}")
        except Exception as e:
            issues.append(f"Articles timestamp test failed: {e}")
            print(f"❌ Articles timestamp test failed: {e}")
        
        # Test user_daily_usage table
        try:
            cursor.execute("SELECT COUNT(*) FROM user_daily_usage")
            count = cursor.fetchone()[0]
            print(f"✅ User daily usage records: {count}")
        except Exception as e:
            issues.append(f"User daily usage test failed: {e}")
            print(f"❌ User daily usage test failed: {e}")
        
        # Test user auth method
        try:
            from user_auth import user_manager
            result = user_manager.get_user_by_id(1)
            print("✅ User authentication method working")
        except Exception as e:
            issues.append(f"User auth method test failed: {e}")
            print(f"❌ User auth method test failed: {e}")
        
        conn.close()
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Verification failed: {e}"]

def main():
    """Apply all fixes"""
    print("🚀 FIXING ALL IDENTIFIED SYSTEM ISSUES")
    print("=" * 60)
    
    fixes = [
        ("Articles Table Schema", fix_articles_table_schema),
        ("User Daily Usage Table", fix_user_daily_usage_table),
        ("User Auth Methods", fix_user_auth_methods),
        ("Database Indexes", create_missing_indexes),
        ("Verification", verify_fixes),
    ]
    
    results = {}
    for fix_name, fix_func in fixes:
        try:
            if fix_name == "Verification":
                success, issues = fix_func()
                results[fix_name] = success
            else:
                results[fix_name] = fix_func()
        except Exception as e:
            print(f"❌ {fix_name} failed: {e}")
            results[fix_name] = False
    
    print("\n" + "=" * 60)
    print("📊 FIX RESULTS SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_fixes = len(results)
    
    for fix_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {fix_name}")
    
    print(f"\n🎯 Overall: {success_count}/{total_fixes} fixes applied successfully")
    
    if success_count == total_fixes:
        print("\n🎉 ALL ISSUES FIXED!")
        print("✅ Database schema corrected")
        print("✅ Missing tables created")
        print("✅ Authentication methods added")
        print("✅ Indexes optimized")
        print("\n🚀 System should now be error-free!")
    else:
        print("\n⚠️ Some fixes failed. Manual intervention may be needed.")

if __name__ == "__main__":
    main()
