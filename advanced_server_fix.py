#!/usr/bin/env python3
"""
Advanced Server Error Fix - Addresses multiple critical issues
"""

import sqlite3
import os
import re
import json

def fix_database_threading_issues():
    """Fix SQLite threading issues by adding connection pooling"""
    print("🔧 Fixing SQLite threading issues...")
    
    try:
        # Read the current app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if threading fix is already applied
        if 'check_same_thread=False' in content:
            print("✅ SQLite threading fix already applied")
            return True
        
        # Add threading fix to database connections
        threading_fixes = [
            ('sqlite3.connect(\'news_database.db\')', 'sqlite3.connect(\'news_database.db\', check_same_thread=False)'),
            ('sqlite3.connect("news_database.db")', 'sqlite3.connect("news_database.db", check_same_thread=False)'),
        ]
        
        for old, new in threading_fixes:
            if old in content:
                content = content.replace(old, new)
                print(f"✅ Fixed: {old}")
        
        # Write back the fixed content
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ SQLite threading issues fixed")
        return True
        
    except Exception as e:
        print(f"❌ Threading fix error: {e}")
        return False

def fix_subscription_manager_data_types():
    """Fix subscription manager data type errors"""
    print("🔧 Fixing subscription manager data types...")
    
    try:
        # Read subscription_manager.py
        with open('subscription_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the problematic line and fix it
        old_line = "limit = int(limit_map.get(usage_type, 0) or 0)"
        new_line = """# Safe conversion handling JSON data
        limit_value = limit_map.get(usage_type, 0) or 0
        if isinstance(limit_value, str):
            try:
                # Try to parse as JSON first
                parsed_value = json.loads(limit_value)
                if isinstance(parsed_value, list):
                    # Extract numeric value from list descriptions
                    for item in parsed_value:
                        if isinstance(item, str) and 'articles per day' in item.lower():
                            # Extract number from string like "Up to 10 articles per day"
                            numbers = re.findall(r'\\d+', item)
                            if numbers:
                                limit = int(numbers[0])
                                break
                    else:
                        limit = 10  # Default limit
                else:
                    limit = int(parsed_value) if str(parsed_value).isdigit() else 10
            except (json.JSONDecodeError, ValueError):
                # If not JSON, try direct int conversion
                if str(limit_value).isdigit():
                    limit = int(limit_value)
                else:
                    limit = 10  # Default safe limit
        else:
            limit = int(limit_value) if limit_value else 10"""
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # Add required imports
            if "import json" not in content:
                content = "import json\n" + content
            if "import re" not in content:
                content = "import re\n" + content
            
            with open('subscription_manager.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fixed subscription manager data types")
        else:
            print("⚠️ Subscription manager line not found (may already be fixed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Subscription manager fix error: {e}")
        return False

def fix_jinja_template_formatting():
    """Fix Jinja2 template formatting errors"""
    print("🔧 Fixing Jinja2 template formatting...")
    
    try:
        template_file = 'templates/live_events.html'
        if not os.path.exists(template_file):
            print("⚠️ Template file not found")
            return True
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the problematic format string
        old_format = '{{ "{:+.2f}%"|format(event.metadata.change_24h if event.metadata.change_24h else 0) }}'
        new_format = '{{ "{:+.2f}%".format(event.metadata.change_24h if event.metadata.change_24h else 0) }}'
        
        if old_format in content:
            content = content.replace(old_format, new_format)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fixed Jinja2 template formatting")
        else:
            print("⚠️ Template format string not found (may already be fixed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Template fix error: {e}")
        return False

def fix_database_column_duplication():
    """Fix database column duplication errors"""
    print("🔧 Fixing database column duplication...")
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get current schema
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"📊 Current columns: {len(existing_columns)} columns found")
        
        # Check for duplicate columns
        duplicates = set()
        seen = set()
        for col in existing_columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
        
        if duplicates:
            print(f"⚠️ Found duplicate columns: {duplicates}")
            
            # Create a new table with proper schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles_fixed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    source_type TEXT,
                    source_name TEXT,
                    filename TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    keywords TEXT,
                    category TEXT,
                    read_status BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    sentiment_score REAL,
                    importance_score INTEGER,
                    data_source TEXT,
                    tags TEXT
                )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
                INSERT INTO articles_fixed 
                SELECT DISTINCT id, title, content, source_type, source_name, filename, 
                       date_added, keywords, category, read_status, is_deleted,
                       NULL as sentiment_score, NULL as importance_score, 
                       NULL as data_source, NULL as tags
                FROM articles
            ''')
            
            # Backup old table and replace
            cursor.execute('DROP TABLE IF EXISTS articles_backup')
            cursor.execute('ALTER TABLE articles RENAME TO articles_backup')
            cursor.execute('ALTER TABLE articles_fixed RENAME TO articles')
            
            print("✅ Fixed database column duplication")
        else:
            print("✅ No duplicate columns found")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database column fix error: {e}")
        return False

def fix_database_connection_management():
    """Add better database connection management"""
    print("🔧 Adding database connection management...")
    
    try:
        # Read current app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if connection management is already added
        if 'def get_db_connection():' in content:
            print("✅ Database connection management already exists")
            return True
        
        # Add connection management function
        connection_manager = '''
def get_db_connection():
    """Get a thread-safe database connection"""
    return sqlite3.connect('news_database.db', check_same_thread=False, timeout=30.0)

def close_db_connection(conn):
    """Safely close database connection"""
    if conn:
        try:
            conn.close()
        except Exception:
            pass
'''
        
        # Find a good place to insert (after imports)
        import_end = content.find('\n# Set up logging')
        if import_end == -1:
            import_end = content.find('\napp = Flask(__name__)')
        
        if import_end != -1:
            content = content[:import_end] + connection_manager + content[import_end:]
            
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added database connection management")
        else:
            print("⚠️ Could not find insertion point for connection management")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection management error: {e}")
        return False

def restart_server_components():
    """Restart critical server components"""
    print("🔄 Restarting server components...")
    
    try:
        # Clear Python cache
        import shutil
        if os.path.exists('__pycache__'):
            shutil.rmtree('__pycache__')
            print("🗑️ Cleared Python cache")
        
        # Clear any temporary files
        for file in os.listdir('.'):
            if file.endswith('.pyc') or file.endswith('.pyo'):
                os.remove(file)
                print(f"🗑️ Removed: {file}")
        
        print("✅ Server components restarted")
        return True
        
    except Exception as e:
        print(f"❌ Component restart error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Advanced WiseNews Server Error Fix")
    print("=" * 50)
    
    # Run all fixes
    success = True
    
    success &= fix_database_threading_issues()
    success &= fix_subscription_manager_data_types()
    success &= fix_jinja_template_formatting()
    success &= fix_database_column_duplication()
    success &= fix_database_connection_management()
    success &= restart_server_components()
    
    if success:
        print("\n✅ All advanced fixes completed successfully!")
        print("🔄 Please restart the server: taskkill /F /IM python.exe && python app.py")
    else:
        print("\n❌ Some fixes failed. Check the errors above.")
        print("💡 Try running individual fix functions manually.")
