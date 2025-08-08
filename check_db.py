import sqlite3

conn = sqlite3.connect('news_database.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:")
for table in tables:
    print(f"  - {table[0]}")

# Check each table for row counts
print("\nTable contents:")
for table in tables:
    table_name = table[0]
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} rows")
        
        if count > 0 and 'news' in table_name.lower():
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample = cursor.fetchall()
            print(f"    Sample data: {len(sample)} rows shown")
    except Exception as e:
        print(f"  {table_name}: Error - {e}")

conn.close()
