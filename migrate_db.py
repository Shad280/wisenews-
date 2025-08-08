"""
Database migration script to fix schema issues
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Fix database schema issues"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # 1. Add publication_status column to generated_articles table
        try:
            cursor.execute('''
                ALTER TABLE generated_articles 
                ADD COLUMN publication_status TEXT DEFAULT 'published'
            ''')
            logger.info("Added publication_status column to generated_articles table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logger.info("publication_status column already exists in generated_articles")
            else:
                logger.error(f"Error adding publication_status column: {e}")
        
        # 2. Check if news table has source_name column (it should use 'source' instead)
        cursor.execute("PRAGMA table_info(news)")
        news_columns = [row[1] for row in cursor.fetchall()]
        
        if 'source_name' not in news_columns:
            logger.info("news table uses 'source' column correctly")
        
        # 3. Check articles table schema
        cursor.execute("PRAGMA table_info(articles)")
        articles_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"articles table columns: {articles_columns}")
        
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database migration: {e}")

if __name__ == "__main__":
    migrate_database()
