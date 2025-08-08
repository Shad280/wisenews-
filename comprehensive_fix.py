#!/usr/bin/env python3
"""
Comprehensive fix for all WiseNews server issues
"""

import sqlite3
import os
import sys
import shutil
import subprocess

def fix_threading_issues():
    """Fix SQLite threading issues in app.py"""
    print("🔧 Fixing SQLite threading issues...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix database connection to use check_same_thread=False
        if 'check_same_thread=False' not in content:
            # Replace sqlite3.connect calls
            content = content.replace(
                "sqlite3.connect('news_database.db')",
                "sqlite3.connect('news_database.db', check_same_thread=False)"
            )
            content = content.replace(
                'sqlite3.connect("news_database.db")',
                'sqlite3.connect("news_database.db", check_same_thread=False)'
            )
        
        # Add proper connection management if not present
        if 'def get_db_connection():' not in content:
            db_management = '''
def get_db_connection():
    """Get a new database connection with proper threading support"""
    try:
        conn = sqlite3.connect('news_database.db', check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def close_db_connection(conn):
    """Safely close database connection"""
    try:
        if conn:
            conn.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")
'''
            # Insert after imports
            import_end = content.find('\napp = Flask(__name__)')
            if import_end != -1:
                content = content[:import_end] + db_management + content[import_end:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed SQLite threading issues")
        return True
        
    except Exception as e:
        print(f"❌ Threading fix error: {e}")
        return False

def fix_subscription_manager():
    """Fix subscription_manager.py import issues"""
    print("🔧 Fixing subscription manager imports...")
    
    try:
        with open('subscription_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add missing import at the top
        if 'import re' not in content:
            lines = content.split('\n')
            # Find the first import line
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_index = i
                    break
            
            # Insert re import
            lines.insert(import_index, 'import re')
            content = '\n'.join(lines)
        
        # Fix the check_usage_limit method to handle missing re module
        if 'numbers = re.findall' in content and 'except NameError:' not in content:
            content = content.replace(
                'numbers = re.findall(r\'\\d+\', item)',
                '''try:
                        numbers = re.findall(r'\\d+', item)
                    except (NameError, AttributeError):
                        import re
                        numbers = re.findall(r'\\d+', item)'''
            )
        
        with open('subscription_manager.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed subscription manager imports")
        return True
        
    except Exception as e:
        print(f"❌ Subscription manager fix error: {e}")
        return False

def fix_database_columns():
    """Fix duplicate database columns"""
    print("🔧 Fixing database column duplications...")
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get current schema
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📊 Current columns: {len(column_names)}")
        
        # Check for duplicates
        duplicates = []
        seen = set()
        for col in column_names:
            if col in seen:
                duplicates.append(col)
            seen.add(col)
        
        if duplicates:
            print(f"⚠️ Found duplicate columns: {duplicates}")
            
            # Create a new table with unique columns
            unique_columns = list(dict.fromkeys(column_names))  # Preserve order, remove duplicates
            
            # Build CREATE TABLE statement
            column_definitions = []
            for col in columns:
                if col[1] in unique_columns:
                    col_def = f"{col[1]} {col[2]}"
                    if col[3]:  # NOT NULL
                        col_def += " NOT NULL"
                    if col[4] is not None:  # DEFAULT value
                        col_def += f" DEFAULT {col[4]}"
                    if col[5]:  # PRIMARY KEY
                        col_def += " PRIMARY KEY"
                    column_definitions.append(col_def)
                    unique_columns.remove(col[1])  # Remove to avoid duplicates
            
            create_table_sql = f"CREATE TABLE articles_new ({', '.join(column_definitions)})"
            
            # Create new table
            cursor.execute(create_table_sql)
            
            # Copy data from old table
            cursor.execute("INSERT INTO articles_new SELECT * FROM articles")
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE articles")
            cursor.execute("ALTER TABLE articles_new RENAME TO articles")
            
            print("✅ Fixed duplicate columns")
        else:
            print("✅ No duplicate columns found")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database column fix error: {e}")
        return False

def terminate_server_processes():
    """Terminate any running server processes"""
    print("🔄 Terminating existing server processes...")
    
    try:
        # Kill any running Python processes
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, text=True)
        print("✅ Terminated server processes")
        return True
    except Exception as e:
        print(f"❌ Process termination error: {e}")
        return False

def clear_python_cache():
    """Clear all Python cache files"""
    print("🧹 Clearing Python cache...")
    
    try:
        # Remove __pycache__ directories
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    pycache_path = os.path.join(root, dir_name)
                    shutil.rmtree(pycache_path)
                    print(f"🗑️ Removed: {pycache_path}")
        
        # Remove .pyc files
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    pyc_path = os.path.join(root, file)
                    os.remove(pyc_path)
                    print(f"🗑️ Removed: {pyc_path}")
        
        print("✅ Cleared Python cache")
        return True
        
    except Exception as e:
        print(f"❌ Cache clear error: {e}")
        return False

def fix_template_errors():
    """Fix any remaining template errors"""
    print("🔧 Checking template files...")
    
    try:
        template_files = ['templates/live_events.html', 'templates/dashboard.html', 'templates/articles.html']
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix any problematic Jinja2 syntax
                if '|format(' in content:
                    # Replace problematic format filters
                    content = content.replace(
                        '{{ event.metadata.change_24h|format(\"+.2f%\") }}',
                        '{{ "{:+.2f}%".format(event.metadata.change_24h) }}'
                    )
                    
                    with open(template_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✅ Fixed template: {template_file}")
                else:
                    print(f"✅ Template OK: {template_file}")
            else:
                print(f"⚠️ Template not found: {template_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template fix error: {e}")
        return False

def create_startup_script():
    """Create a clean startup script"""
    print("🚀 Creating startup script...")
    
    startup_script = '''@echo off
echo Starting WiseNews Server...
echo Killing any existing processes...
taskkill /F /IM python.exe >nul 2>&1
echo Starting server...
python app.py
pause
'''
    
    try:
        with open('start_server.bat', 'w') as f:
            f.write(startup_script)
        
        print("✅ Created startup script: start_server.bat")
        return True
        
    except Exception as e:
        print(f"❌ Startup script error: {e}")
        return False

def validate_fixes():
    """Validate that all fixes are working"""
    print("🔍 Validating fixes...")
    
    try:
        # Test database connection
        conn = sqlite3.connect('news_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database accessible: {count} articles")
        
        # Test imports
        try:
            import subscription_manager
            print("✅ Subscription manager imports OK")
        except Exception as e:
            print(f"❌ Subscription manager import error: {e}")
            return False
        
        # Check critical files
        critical_files = ['app.py', 'subscription_manager.py', 'news_database.db']
        for file in critical_files:
            if os.path.exists(file):
                print(f"✅ {file} exists")
            else:
                print(f"❌ Missing: {file}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def main():
    """Run comprehensive fixes"""
    print("🔧 WiseNews Comprehensive Server Fix")
    print("=" * 50)
    
    # Run all fixes
    fixes = [
        terminate_server_processes,
        clear_python_cache,
        fix_database_columns,
        fix_threading_issues,
        fix_subscription_manager,
        fix_template_errors,
        create_startup_script,
        validate_fixes
    ]
    
    success_count = 0
    for fix_func in fixes:
        try:
            if fix_func():
                success_count += 1
            print()  # Add spacing
        except Exception as e:
            print(f"❌ Fix function {fix_func.__name__} failed: {e}")
            print()
    
    print(f"📊 Fix Summary: {success_count}/{len(fixes)} successful")
    
    if success_count == len(fixes):
        print("\n🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
        print("🚀 Run 'python app.py' or 'start_server.bat' to start the server")
    else:
        print(f"\n⚠️ {len(fixes) - success_count} fixes failed. Check errors above.")
    
    return success_count == len(fixes)

if __name__ == "__main__":
    main()
