#!/usr/bin/env python3
"""
Fix database schema issues and server errors
"""

import sqlite3
import os
import re

# Try to import langdetect, fallback to regex if not available
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

def is_english_text(text):
    """Check if text is in English"""
    if not text or len(text.strip()) < 20:
        return False
    
    # Use langdetect if available
    if LANGDETECT_AVAILABLE:
        try:
            # Clean text for language detection
            clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if len(clean_text) < 10:
                return False
            
            # Detect language
            language = detect(clean_text)
            return language == 'en'
        except (LangDetectException, Exception):
            pass  # Fall through to regex method
    
    # Fallback regex-based detection
    # Check for common non-English patterns
    non_english_patterns = [
        r'[א-ת]',  # Hebrew
        r'[ا-ي]',  # Arabic
        r'[一-龯]',  # Chinese
        r'[ひらがな]',  # Japanese Hiragana
        r'[カタカナ]',  # Japanese Katakana
        r'[가-힣]',  # Korean
        r'[ก-๙]',  # Thai
        r'[А-я]',  # Cyrillic
        r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]',  # Extended Latin (French, German, etc.)
    ]
    
    for pattern in non_english_patterns:
        if re.search(pattern, text):
            return False
    
    # Basic English word check
    english_indicators = [
        'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 
        'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 
        'at', 'be', 'or', 'an', 'have', 'from', 'this', 'by', 'had',
        'but', 'not', 'what', 'all', 'were', 'we', 'can', 'said',
        'there', 'each', 'which', 'she', 'do', 'how', 'their', 'will'
    ]
    
    # Clean and split text
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    text_words = clean_text.split()
    
    if len(text_words) < 5:
        return False
    
    # Count English indicator words
    english_word_count = sum(1 for word in text_words if word in english_indicators)
    english_ratio = english_word_count / len(text_words)
    
    # Require at least 5% English indicator words
    return english_ratio >= 0.05

def is_small_update(title, content):
    """Check if article is a small update that should be a notification"""
    if not title:
        return True
    
    # Check content length
    content_length = len(content.strip()) if content else 0
    title_length = len(title.strip())
    
    # Very short content
    if content_length < 100:
        return True
    
    # Short titles that are typically updates
    if title_length < 50:
        update_patterns = [
            r'\b(update|breaking|alert|urgent|live|now)\b',
            r'\b\d+%?\s*(up|down|rise|fall|drop|jump)\b',
            r'\b(q\d|quarter)\s*(revenue|earnings|profit)\b',
            r'\$\d+[kmb]?\s*(revenue|profit|loss)\b',
            r'\b(wins?|loses?|beats?|misses?)\s*(estimate|expectation)\b',
        ]
        
        for pattern in update_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
    
    # Check for stock/financial update patterns
    financial_patterns = [
        r'\([A-Z]{3,5}\)\s*Q\d',  # Stock ticker with quarter
        r'\b\d+%\b',  # Percentage
        r'\$\d+[.,]?\d*[kmbt]?\b',  # Dollar amounts
    ]
    
    for pattern in financial_patterns:
        if re.search(pattern, title):
            return True
    
    return False

def create_notification_table():
    """Create notifications table for small updates"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT,
                source_name TEXT,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                priority INTEGER DEFAULT 1,
                notification_type TEXT DEFAULT 'update'
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Notifications table created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating notifications table: {e}")
        return False

def filter_non_english_articles():
    """Remove non-English articles from database"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        print("🔍 Checking articles for language...")
        
        # Get all articles
        cursor.execute("SELECT id, title, content FROM articles WHERE is_deleted IS NOT 1 OR is_deleted IS NULL")
        articles = cursor.fetchall()
        
        non_english_count = 0
        small_update_count = 0
        
        for article_id, title, content in articles:
            # Check if English
            combined_text = f"{title} {content}" if content else title
            
            if not is_english_text(combined_text):
                # Mark as deleted instead of actually deleting
                cursor.execute("UPDATE articles SET is_deleted = 1 WHERE id = ?", (article_id,))
                non_english_count += 1
                print(f"🗑️ Marked non-English article: {title[:50]}...")
            elif is_small_update(title, content):
                # Move to notifications
                cursor.execute("""
                    INSERT INTO notifications (title, content, category, source_name, notification_type)
                    SELECT title, content, category, source_name, 'update'
                    FROM articles WHERE id = ?
                """, (article_id,))
                
                # Mark original as deleted
                cursor.execute("UPDATE articles SET is_deleted = 1 WHERE id = ?", (article_id,))
                small_update_count += 1
                print(f"📱 Moved to notifications: {title[:50]}...")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Filtered {non_english_count} non-English articles")
        print(f"✅ Moved {small_update_count} small updates to notifications")
        return True
        
    except Exception as e:
        print(f"❌ Error filtering articles: {e}")
        return False

def clean_downloaded_files():
    """Remove non-English downloaded files"""
    try:
        downloads_dir = "downloads"
        if not os.path.exists(downloads_dir):
            return True
            
        print("🧹 Cleaning non-English downloaded files...")
        
        files_removed = 0
        for filename in os.listdir(downloads_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(downloads_dir, filename)
                
                # Check for non-English patterns in filename
                non_english_patterns = [
                    r'[א-ת]',  # Hebrew
                    r'[ا-ي]',  # Arabic  
                    r'[一-龯]',  # Chinese
                    r'[ก-๙]',  # Thai
                    r'[А-я]',  # Cyrillic
                ]
                
                should_remove = False
                for pattern in non_english_patterns:
                    if re.search(pattern, filename):
                        should_remove = True
                        break
                
                if should_remove:
                    try:
                        os.remove(file_path)
                        files_removed += 1
                        print(f"🗑️ Removed: {filename[:50]}...")
                    except Exception as e:
                        print(f"⚠️ Could not remove {filename}: {e}")
        
        print(f"✅ Removed {files_removed} non-English files")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning files: {e}")
        return False

def fix_database_schema():
    """Fix database schema issues"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        print("🔧 Checking and fixing database schema...")
        
        # Check current schema
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"📊 Current columns: {existing_columns}")
        
        # Check for problematic columns that might be causing issues
        required_columns = {
            'sentiment_score': 'REAL',
            'importance_score': 'INTEGER', 
            'data_source': 'TEXT',
            'tags': 'TEXT'
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"➕ Adding missing columns: {missing_columns}")
            for col_name, col_type in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️ Column {col_name} already exists")
                    else:
                        print(f"❌ Error adding column {col_name}: {e}")
        else:
            print("✅ All required columns exist")
        
        # Check for corrupted indexes
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity != 'ok':
            print(f"⚠️ Database integrity issue: {integrity}")
        else:
            print("✅ Database integrity OK")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database fix error: {e}")
        return False

def clear_flask_cache():
    """Clear Flask application cache"""
    try:
        print("🧹 Clearing Flask cache...")
        
        # Remove cache files
        cache_patterns = [
            '__pycache__/',
            '*.pyc',
            'flask_session/',
            '.cache/',
            'cache/'
        ]
        
        import glob
        files_removed = 0
        
        for pattern in cache_patterns:
            if pattern.endswith('/'):
                # Directory
                if os.path.exists(pattern):
                    import shutil
                    shutil.rmtree(pattern)
                    files_removed += 1
                    print(f"🗑️ Removed directory: {pattern}")
            else:
                # Files
                for file in glob.glob(pattern):
                    os.remove(file)
                    files_removed += 1
                    print(f"🗑️ Removed file: {file}")
        
        print(f"✅ Cleared {files_removed} cache items")
        return True
        
    except Exception as e:
        print(f"❌ Cache clear error: {e}")
        return False

def fix_unicode_logging():
    """Create a fix for unicode logging issues"""
    try:
        print("🔤 Fixing Unicode logging issues...")
        
        # Create a logging configuration that handles Unicode properly
        logging_fix = '''
import logging
import sys

# Configure logging to handle Unicode properly on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set UTF-8 encoding for stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
'''
        
        with open('logging_fix.py', 'w', encoding='utf-8') as f:
            f.write(logging_fix)
        
        print("✅ Created Unicode logging fix")
        return True
        
    except Exception as e:
        print(f"❌ Unicode fix error: {e}")
        return False

def validate_server_config():
    """Validate server configuration"""
    try:
        print("⚙️ Validating server configuration...")
        
        # Check critical files
        critical_files = [
            'app.py',
            'news_database.db',
            'templates/dashboard.html',
            'templates/articles.html'
        ]
        
        for file in critical_files:
            if os.path.exists(file):
                print(f"✅ {file} exists")
            else:
                print(f"❌ Missing critical file: {file}")
                return False
        
        # Check database accessibility
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        print(f"📊 Database has {count} articles")
        conn.close()
        
        print("✅ Server configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 WiseNews Server Error Fix & Language Filter")
    print("=" * 50)
    
    # Install required package
    print("📦 Installing language detection package...")
    try:
        import subprocess
        result = subprocess.run(['pip', 'install', 'langdetect'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ langdetect package installed successfully")
        else:
            print("⚠️ Using fallback language detection (regex-based)")
    except Exception as e:
        print(f"⚠️ Could not install langdetect: {e}")
    
    # Run fixes
    success = True
    
    success &= fix_database_schema()
    success &= clear_flask_cache() 
    success &= fix_unicode_logging()
    success &= validate_server_config()
    
    # New language and content filtering
    success &= create_notification_table()
    success &= filter_non_english_articles()
    success &= clean_downloaded_files()
    
    if success:
        print("\n✅ All fixes completed successfully!")
        print("📈 Database now contains only English articles")
        print("📱 Small updates moved to notifications")
        print("🔄 Please restart the server with: python app.py")
    else:
        print("\n❌ Some fixes failed. Check the errors above.")
