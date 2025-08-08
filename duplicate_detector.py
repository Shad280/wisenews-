"""
Duplicate Article Detection and Removal System
Analyzes articles for duplicates and keeps the most relevant ones
"""

import sqlite3
import hashlib
import re
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self, db_path='news_database.db'):
        self.db_path = db_path
        self.similarity_threshold = 0.85  # 85% similarity threshold
        self.title_similarity_threshold = 0.9  # 90% for titles
        
    def connect_db(self):
        """Connect to the database"""
        return sqlite3.connect(self.db_path)
    
    def normalize_text(self, text):
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters except alphanumeric and spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        return text.strip()
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        # Calculate sequence similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def get_content_hash(self, content):
        """Generate a hash for content comparison"""
        if not content:
            return ""
        
        normalized = self.normalize_text(content)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def analyze_articles(self):
        """Analyze all articles for duplicates"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Check which table has the articles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('news', 'articles')")
        tables = cursor.fetchall()
        
        table_name = None
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            if count > 0:
                table_name = table[0]
                break
        
        if not table_name:
            print("❌ No articles found in database")
            conn.close()
            return []
        
        print(f"📊 Using table: {table_name}")
        
        # Get all articles
        cursor.execute(f'''
            SELECT id, title, content, url_hash, source_name, date_added, 
                   COALESCE(importance_score, 5) as relevance_score, 
                   COALESCE(sentiment_score, 0.0) as sentiment_score, 
                   COALESCE(date_added, date_added) as last_updated
            FROM {table_name}
            ORDER BY date_added DESC
        ''')
        
        articles = cursor.fetchall()
        conn.close()
        
        print(f"📊 Analyzing {len(articles)} articles for duplicates...")
        
        # Group articles for duplicate detection
        duplicates = self.find_duplicates(articles)
        
        return duplicates, table_name
    
    def find_duplicates(self, articles):
        """Find duplicate articles using multiple criteria"""
        duplicates = []
        processed_ids = set()
        
        print("🔍 Detecting duplicates...")
        
        for i, article1 in enumerate(articles):
            if article1[0] in processed_ids:
                continue
                
            duplicate_group = [article1]
            processed_ids.add(article1[0])
            
            for j, article2 in enumerate(articles[i+1:], i+1):
                if article2[0] in processed_ids:
                    continue
                
                is_duplicate = self.is_duplicate(article1, article2)
                
                if is_duplicate:
                    duplicate_group.append(article2)
                    processed_ids.add(article2[0])
            
            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)
                print(f"🔄 Found duplicate group with {len(duplicate_group)} articles")
        
        return duplicates
    
    def is_duplicate(self, article1, article2):
        """Check if two articles are duplicates"""
        # Extract data
        id1, title1, content1, url1, source1, date1, relevance1, views1, updated1 = article1
        id2, title2, content2, url2, source2, date2, relevance2, views2, updated2 = article2
        
        # Check for exact URL match
        if url1 and url2 and url1 == url2:
            return True
        
        # Check title similarity
        title_similarity = self.calculate_similarity(title1, title2)
        if title_similarity >= self.title_similarity_threshold:
            # If titles are very similar, check content
            content_similarity = self.calculate_similarity(content1, content2)
            if content_similarity >= self.similarity_threshold:
                return True
        
        # Check content hash for exact content matches
        if content1 and content2:
            hash1 = self.get_content_hash(content1)
            hash2 = self.get_content_hash(content2)
            if hash1 == hash2 and hash1 != "":
                return True
        
        # Check for very high content similarity even with different titles
        if content1 and content2:
            content_similarity = self.calculate_similarity(content1, content2)
            if content_similarity >= 0.95:  # 95% content similarity
                return True
        
        return False
    
    def select_best_article(self, duplicate_group):
        """Select the best article from a duplicate group"""
        if len(duplicate_group) == 1:
            return duplicate_group[0]
        
        # Scoring criteria
        best_article = None
        best_score = -1
        
        for article in duplicate_group:
            # Updated indices for articles table: id, title, content, url_hash, source_name, date_added, importance_score, sentiment_score, last_updated
            id_, title, content, url_hash, source_name, date_added, importance_score, sentiment_score, last_updated = article
            
            score = 0
            
            # Content length (longer is often better)
            if content:
                score += min(len(content) / 1000, 5)  # Max 5 points for content length
            
            # Importance score (1-10 scale)
            if importance_score:
                score += importance_score / 2  # Max 5 points for importance
            
            # Sentiment score (positive sentiment preferred for news)
            if sentiment_score and sentiment_score > 0:
                score += min(sentiment_score * 2, 1)  # Max 1 point for positive sentiment
            
            # Source reputation (prefer major sources)
            reputable_sources = ['bbc', 'cnn', 'reuters', 'ap', 'nytimes', 'guardian', 'washingtonpost']
            if source_name:
                for rep_source in reputable_sources:
                    if rep_source in source_name.lower():
                        score += 2
                        break
            
            # Recency (prefer newer articles)
            if date_added:
                try:
                    from datetime import datetime
                    article_date = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                    days_old = (datetime.now() - article_date.replace(tzinfo=None)).days
                    if days_old <= 1:
                        score += 3
                    elif days_old <= 7:
                        score += 1
                except:
                    pass
            
            # Title quality (prefer longer, more descriptive titles)
            if title:
                score += min(len(title) / 50, 1)  # Max 1 point for title length
            
            if score > best_score:
                best_score = score
                best_article = article
        
        return best_article
    
    def remove_duplicates(self, duplicates, dry_run=True):
        """Remove duplicate articles, keeping the best ones"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        total_removed = 0
        total_kept = 0
        
        print(f"🗑️  Processing {len(duplicates)} duplicate groups...")
        
        for group in duplicates:
            best_article = self.select_best_article(group)
            best_id = best_article[0]
            
            articles_to_remove = [article[0] for article in group if article[0] != best_id]
            
            print(f"\n📰 Duplicate group of {len(group)} articles:")
            print(f"   ✅ Keeping: ID {best_id} - \"{best_article[1][:60]}...\"")
            
            for article_id in articles_to_remove:
                article = next(a for a in group if a[0] == article_id)
                print(f"   ❌ Removing: ID {article_id} - \"{article[1][:60]}...\"")
                
                if not dry_run:
                    cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
                
                total_removed += 1
            
            total_kept += 1
        
        if not dry_run:
            conn.commit()
            print(f"\n✅ Database changes committed!")
        else:
            print(f"\n🔍 DRY RUN - No changes made to database")
        
        conn.close()
        
        print(f"\n📊 Summary:")
        print(f"   📰 Articles kept: {total_kept}")
        print(f"   🗑️  Articles removed: {total_removed}")
        print(f"   💾 Space saved: ~{total_removed * 2}KB")
        
        return total_removed, total_kept
    
    def analyze_by_source(self):
        """Analyze duplicates by source"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM news
            GROUP BY source
            ORDER BY count DESC
            LIMIT 20
        ''')
        
        sources = cursor.fetchall()
        conn.close()
        
        print("\n📊 Articles by source (top 20):")
        for source, count in sources:
            print(f"   {source}: {count} articles")
        
        return sources
    
    def find_near_duplicates(self):
        """Find articles that are very similar but not exact duplicates"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, source
            FROM news
            ORDER BY published_date DESC
            LIMIT 1000
        ''')
        
        articles = cursor.fetchall()
        conn.close()
        
        near_duplicates = []
        processed = set()
        
        print("🔍 Finding near-duplicates (75-85% similarity)...")
        
        for i, article1 in enumerate(articles):
            if article1[0] in processed:
                continue
                
            for j, article2 in enumerate(articles[i+1:], i+1):
                if article2[0] in processed:
                    continue
                
                title_sim = self.calculate_similarity(article1[1], article2[1])
                content_sim = self.calculate_similarity(article1[2], article2[2])
                
                # Near duplicate if high similarity but below duplicate threshold
                if (0.75 <= title_sim < self.title_similarity_threshold or 
                    0.75 <= content_sim < self.similarity_threshold):
                    
                    near_duplicates.append((article1, article2, title_sim, content_sim))
                    print(f"📄 Near-duplicate: \"{article1[1][:40]}...\" vs \"{article2[1][:40]}...\" (T:{title_sim:.2f}, C:{content_sim:.2f})")
        
        return near_duplicates
    
    def cleanup_empty_articles(self):
        """Remove articles with empty or very short content"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Find articles with empty or very short content
        cursor.execute('''
            SELECT id, title, content, source
            FROM news
            WHERE content IS NULL 
               OR LENGTH(content) < 50
               OR title IS NULL
               OR LENGTH(title) < 10
        ''')
        
        empty_articles = cursor.fetchall()
        
        print(f"🧹 Found {len(empty_articles)} articles with insufficient content")
        
        for article in empty_articles[:10]:  # Show first 10
            print(f"   📄 ID {article[0]}: \"{article[1] or 'NO TITLE'}\" ({len(article[2] or '')} chars)")
        
        if empty_articles:
            response = input(f"\n❓ Remove {len(empty_articles)} low-quality articles? (y/N): ")
            if response.lower() == 'y':
                cursor.execute('''
                    DELETE FROM news
                    WHERE content IS NULL 
                       OR LENGTH(content) < 50
                       OR title IS NULL
                       OR LENGTH(title) < 10
                ''')
                conn.commit()
                print(f"✅ Removed {len(empty_articles)} low-quality articles")
        
        conn.close()
        return len(empty_articles)

def main():
    """Main function to run duplicate detection"""
    detector = DuplicateDetector()
    
    print("🔍 WiseNews Duplicate Article Detector")
    print("=" * 50)
    
    # Analyze current database
    print("\n1. Analyzing database...")
    duplicates, table_name = detector.analyze_articles()
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    conn = detector.connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    total_articles = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(DISTINCT title) FROM {table_name}')
    unique_titles = cursor.fetchone()[0]
    
    cursor.execute(f'SELECT COUNT(DISTINCT url_hash) FROM {table_name} WHERE url_hash IS NOT NULL')
    unique_urls = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"📊 Database Statistics:")
    print(f"   Table: {table_name}")
    print(f"   Total articles: {total_articles}")
    print(f"   Unique titles: {unique_titles}")
    print(f"   Unique URL hashes: {unique_urls}")
    print(f"   Duplicate groups found: {len(duplicates)}")
    
    # Show preview
    print(f"\n2. Found {len(duplicates)} duplicate groups")
    
    # Ask user what to do
    print("\n🔧 What would you like to do?")
    print("1. Preview duplicates (dry run)")
    print("2. Remove duplicates (actual deletion)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        detector.remove_duplicates(duplicates, dry_run=True)
    elif choice == '2':
        detector.remove_duplicates(duplicates, dry_run=False)
    else:
        print("👋 Exiting...")

if __name__ == "__main__":
    main()
