import sqlite3

def debug_database():
    conn = sqlite3.connect('news_database.db')
    cursor = conn.cursor()
    
    print('🔍 SUBSCRIPTION PLANS TABLE STRUCTURE:')
    cursor.execute("PRAGMA table_info(subscription_plans)")
    columns = cursor.fetchall()
    for col in columns:
        print(f'   Column: {col[1]} | Type: {col[2]} | Not Null: {col[3]} | Default: {col[4]}')
    
    print('\n📊 SUBSCRIPTION PLANS DATA:')
    cursor.execute('SELECT * FROM subscription_plans')
    plans = cursor.fetchall()
    for plan in plans:
        print(f'   Plan {plan[0]}: {plan}')
    
    print('\n🔍 USER SUBSCRIPTIONS JOIN QUERY:')
    cursor.execute('''
        SELECT us.*, sp.* 
        FROM user_subscriptions us 
        JOIN subscription_plans sp ON us.plan_id = sp.id 
        WHERE us.user_id = 2
    ''')
    result = cursor.fetchone()
    if result:
        print(f'   Raw result: {result}')
        print(f'   Length: {len(result)}')
        if len(result) >= 15:
            print(f'   max_articles_per_day value: "{result[13]}" (type: {type(result[13])})')
    
    conn.close()

if __name__ == "__main__":
    debug_database()
