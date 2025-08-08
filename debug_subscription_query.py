import sqlite3

def debug_subscription_query():
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    print('🔍 DEBUGGING SUBSCRIPTION QUERY COLUMN MAPPING:')
    cursor.execute('''
        SELECT us.*, sp.name, sp.display_name, sp.features, sp.max_articles_per_day,
               sp.max_searches_per_day, sp.max_bookmarks, sp.api_access,
               sp.priority_support, sp.advanced_filters, sp.export_data
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE us.user_id = 2 AND us.status IN ('active', 'trial')
        ORDER BY us.created_at DESC
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    if result:
        print(f'Total columns: {len(result)}')
        for i, value in enumerate(result):
            print(f'   Index {i}: {value} (type: {type(value)})')
    
    print('\n🔍 USER_SUBSCRIPTIONS TABLE STRUCTURE:')
    cursor.execute("PRAGMA table_info(user_subscriptions)")
    us_columns = cursor.fetchall()
    for i, col in enumerate(us_columns):
        print(f'   us[{i}]: {col[1]} | Type: {col[2]}')
    
    print('\n🔍 SUBSCRIPTION_PLANS COLUMNS BEING SELECTED:')
    sp_columns = ['name', 'display_name', 'features', 'max_articles_per_day',
                  'max_searches_per_day', 'max_bookmarks', 'api_access',
                  'priority_support', 'advanced_filters', 'export_data']
    
    us_col_count = len(us_columns)
    for i, col in enumerate(sp_columns):
        index = us_col_count + i
        print(f'   result[{index}]: sp.{col}')
    
    conn.close()

if __name__ == "__main__":
    debug_subscription_query()
