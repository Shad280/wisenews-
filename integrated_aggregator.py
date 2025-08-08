"""
Enhanced News Aggregator Integration
Integrates all data sources with existing WiseNews system
"""

import requests
import json
import sqlite3
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import feedparser
from bs4 import BeautifulSoup
import schedule
from collections import defaultdict
from database_manager import db_manager

logger = logging.getLogger(__name__)

class IntegratedDataAggregator:
    def __init__(self):
        # API Keys (to be configured)
        self.api_keys = {
            'newsapi': 'your_newsapi_key',
            'alpha_vantage': 'your_alpha_vantage_key',
            'coinmarketcap': 'your_coinmarketcap_key',
            'reddit': {'client_id': 'your_reddit_client_id', 'client_secret': 'your_reddit_secret'},
            'youtube': 'your_youtube_api_key',
            'twitter': {'bearer_token': 'your_twitter_bearer_token'},
            'quandl': 'your_quandl_key',
            'fred': 'your_fred_api_key'
        }
        
        # Additional data sources
        self.enhanced_sources = {
            'news_apis': [
                {
                    'name': 'NewsAPI',
                    'url': 'https://newsapi.org/v2/everything',
                    'active': False,
                    'params_func': self._newsapi_params
                },
                {
                    'name': 'CoinGecko',
                    'url': 'https://api.coingecko.com/api/v3/coins/markets',
                    'active': True,
                    'params_func': self._coingecko_params
                }
            ],
            'reddit_sources': [
                'worldnews', 'news', 'politics', 'economics', 
                'cryptocurrency', 'stocks', 'technology'
            ],
            'government_sources': [
                {
                    'name': 'Federal Reserve',
                    'url': 'https://www.federalreserve.gov/feeds/press_all.xml',
                    'type': 'rss'
                },
                {
                    'name': 'SEC',
                    'url': 'https://www.sec.gov/news/pressreleases.rss',
                    'type': 'rss'
                }
            ]
        }
        
        # Initialize enhanced database
        self._init_enhanced_db()
        
        # Live data cache
        self.live_cache = defaultdict(list)
        self.cache_lock = threading.Lock()
        
        self.running = True
    
    def _init_enhanced_db(self):
        """Initialize enhanced database tables"""
        try:
            # Check if columns already exist before adding them
            existing_columns = db_manager.execute_query("PRAGMA table_info(articles)")
            column_names = [col[1] for col in existing_columns] if existing_columns else []
            
            # Only add columns if they don't exist
            columns_to_add = [
                ('sentiment_score', 'REAL DEFAULT 0.0'),
                ('importance_score', 'INTEGER DEFAULT 5'),
                ('data_source', 'TEXT DEFAULT "RSS"'),
                ('tags', 'TEXT')
            ]
            
            for col_name, col_definition in columns_to_add:
                if col_name not in column_names:
                    try:
                        db_manager.execute_query(f'ALTER TABLE articles ADD COLUMN {col_name} {col_definition}')
                        logger.info(f"Added column: {col_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e):
                            logger.warning(f"Could not add column {col_name}: {e}")
                else:
                    logger.debug(f"Column {col_name} already exists")
            
            logger.info("Enhanced database structure initialized")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced database: {e}")
    
    def _newsapi_params(self):
        """NewsAPI parameters"""
        return {
            'apiKey': self.api_keys['newsapi'],
            'q': 'breaking OR urgent OR market OR crypto OR politics',
            'sortBy': 'publishedAt',
            'pageSize': 50
        }
    
    def _coingecko_params(self):
        """CoinGecko parameters"""
        return {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 50,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
    
    def fetch_newsapi_articles(self):
        """Fetch from NewsAPI"""
        if self.api_keys['newsapi'] == 'your_newsapi_key':
            return []
        
        try:
            response = requests.get(
                'https://newsapi.org/v2/everything',
                params=self._newsapi_params(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', ''),
                        'content': article.get('description', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': f"NewsAPI - {article.get('source', {}).get('name', 'Unknown')}",
                        'category': 'news',
                        'data_source': 'NewsAPI',
                        'source_type': 'news_api',
                        'importance_score': 6
                    })
                
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
            return []
    
    def fetch_coingecko_data(self):
        """Fetch cryptocurrency data from CoinGecko"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/coins/markets',
                params=self._coingecko_params(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                updates = []
                
                for coin in data:
                    price_change = coin.get('price_change_percentage_24h', 0)
                    if abs(price_change) > 3:  # Significant changes only
                        importance = 8 if abs(price_change) > 10 else 6
                        
                        updates.append({
                            'title': f"{coin['name']} ({coin['symbol'].upper()}) - {price_change:.2f}% in 24h",
                            'content': f"Current price: ${coin['current_price']}, Market cap: ${coin['market_cap']:,}, 24h change: {price_change:.2f}%",
                            'url': f"https://www.coingecko.com/en/coins/{coin['id']}",
                            'source': 'CoinGecko',
                            'category': 'crypto',
                            'data_source': 'CoinGecko',
                            'source_type': 'crypto_api',
                            'importance_score': importance,
                            'tags': f"cryptocurrency,{coin['symbol']},price-alert"
                        })
                
                return updates
                
        except Exception as e:
            logger.error(f"Error fetching CoinGecko: {e}")
            return []
    
    def fetch_reddit_data(self):
        """Fetch trending posts from Reddit"""
        try:
            articles = []
            
            for subreddit in self.enhanced_sources['reddit_sources']:
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                    headers = {'User-Agent': 'WiseNews/1.0'}
                    
                    response = requests.get(url, headers=headers, params={'limit': 5}, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for post in data['data']['children']:
                            post_data = post['data']
                            score = post_data.get('score', 0)
                            
                            if score > 500:  # Popular posts only
                                importance = min(9, max(5, score // 200))
                                
                                articles.append({
                                    'title': post_data.get('title', ''),
                                    'content': post_data.get('selftext', '')[:500] or f"Popular discussion in r/{subreddit}",
                                    'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                                    'source': f"Reddit r/{subreddit}",
                                    'category': 'social',
                                    'data_source': 'Reddit',
                                    'source_type': 'social_media',
                                    'importance_score': importance,
                                    'tags': f"reddit,{subreddit},discussion"
                                })
                
                except Exception as e:
                    logger.error(f"Error fetching r/{subreddit}: {e}")
                    continue
                
                time.sleep(1)  # Rate limiting
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return []
    
    def fetch_government_feeds(self):
        """Fetch government and regulatory feeds"""
        articles = []
        
        for source in self.enhanced_sources['government_sources']:
            try:
                if source['type'] == 'rss':
                    feed = feedparser.parse(source['url'])
                    
                    for entry in feed.entries[:5]:  # Limit per source
                        articles.append({
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'published_at': entry.get('published', ''),
                            'source': source['name'],
                            'category': 'government',
                            'data_source': 'Government',
                            'source_type': 'government_feed',
                            'importance_score': 7,
                            'tags': 'government,regulatory,official'
                        })
                
            except Exception as e:
                logger.error(f"Error fetching {source['name']}: {e}")
                continue
        
        return articles
    
    def save_enhanced_articles(self, articles):
        """Save articles with enhanced metadata"""
        if not articles:
            return 0
        
        saved_count = 0
        
        for article in articles:
            try:
                # Check for duplicates
                existing = db_manager.execute_query(
                    'SELECT id FROM articles WHERE title = ? AND source_name = ?', 
                    (article['title'], article['source']),
                    fetch='one'
                )
                
                if existing:
                    continue  # Skip duplicates
                
                # Generate filename
                safe_title = "".join(c for c in article['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{article['data_source']}_{safe_title}_{timestamp}.txt"
                
                # Insert article with all required fields
                file_path = f"articles/{filename}"  # Create file path
                source_type = article.get('source_type', 'api')  # Default to 'api' type
                
                db_manager.execute_query('''
                    INSERT INTO articles (title, content, source_type, source_name, category, url_hash, 
                                        filename, file_path, sentiment_score, importance_score, data_source, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'],
                    article['content'],
                    source_type,
                    article['source'],
                    article['category'],
                    article.get('url', ''),
                    filename,
                    file_path,
                    article.get('sentiment_score', 0.0),
                    article.get('importance_score', 5),
                    article['data_source'],
                    article.get('tags', '')
                ))
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving article: {e}")
                continue
        
        return saved_count
    
    def create_live_feed_update(self, article):
        """Create live feed update from article"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO live_feeds (feed_type, source, title, content, importance_score, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article['category'],
                article['source'],
                article['title'],
                article['content'],
                article.get('importance_score', 5),
                article.get('tags', '')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating live feed update: {e}")
    
    def aggregate_enhanced_sources(self):
        """Aggregate from all enhanced sources"""
        try:
            all_articles = []
            
            # Fetch from NewsAPI
            articles = self.fetch_newsapi_articles()
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            
            # Fetch crypto data
            articles = self.fetch_coingecko_data()
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} crypto updates from CoinGecko")
            
            # Fetch Reddit data
            articles = self.fetch_reddit_data()
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} posts from Reddit")
            
            # Fetch government feeds
            articles = self.fetch_government_feeds()
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} government updates")
            
            # Save articles
            saved_count = self.save_enhanced_articles(all_articles)
            
            # Create live feed updates for important articles
            for article in all_articles:
                if article.get('importance_score', 5) >= 7:
                    self.create_live_feed_update(article)
            
            logger.info(f"Enhanced aggregation completed: {saved_count} new articles saved")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error in enhanced aggregation: {e}")
            return 0
    
    def start_enhanced_aggregation(self):
        """Start enhanced data aggregation with scheduling"""
        def run_aggregation():
            try:
                self.aggregate_enhanced_sources()
            except Exception as e:
                logger.error(f"Error in scheduled enhanced aggregation: {e}")
        
        # Schedule enhanced aggregation
        schedule.every(15).minutes.do(run_aggregation)  # More frequent for live data
        
        def scheduler_loop():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        
        logger.info("Enhanced data aggregation started with 15-minute intervals")
    
    def stop(self):
        """Stop enhanced aggregation"""
        self.running = False
        logger.info("Enhanced aggregation stopped")

# Global instance
integrated_aggregator = IntegratedDataAggregator()

def start_integrated_aggregation():
    """Start the integrated enhanced aggregation system"""
    integrated_aggregator.start_enhanced_aggregation()
    logger.info("Integrated Enhanced Data Aggregation System started")

# Update the aggregate_news function to include enhanced sources
def aggregate_news():
    """Enhanced news aggregation function"""
    try:
        # Run original RSS aggregation
        from news_aggregator import run_pipeline
        run_pipeline()
        
        # Run enhanced aggregation
        integrated_aggregator.aggregate_enhanced_sources()
        
        logger.info("Complete news aggregation (RSS + Enhanced sources) completed")
        
    except Exception as e:
        logger.error(f"Error in aggregate_news: {e}")

if __name__ == "__main__":
    start_integrated_aggregation()
