"""
Enhanced Data Aggregator for WiseNews
Integrates all major data sources and live feeds for comprehensive news coverage
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
import asyncio
import aiohttp
import websocket
import schedule
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnhancedDataAggregator:
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
            'fred': 'your_fred_api_key',
            'polygon': 'your_polygon_key',
            'iex': 'your_iex_token',
            'finnhub': 'your_finnhub_key'
        }
        
        # Live feed configurations
        self.live_feeds = {
            'crypto_websockets': [
                'wss://stream.binance.com:9443/ws/btcusdt@ticker',
                'wss://ws-feed.pro.coinbase.com'
            ],
            'stock_websockets': [
                'wss://ws.finnhub.io?token={finnhub_key}',
                'wss://socket.polygon.io/stocks'
            ],
            'news_websockets': [
                'wss://ws.newsapi.org/v2/everything'
            ]
        }
        
        # Data sources configuration
        self.data_sources = self._init_data_sources()
        
        # Live feed storage
        self.live_data_cache = defaultdict(list)
        self.cache_lock = threading.Lock()
        
        # Initialize database
        self._init_live_feeds_db()
        
        # Start live feeds
        self.websocket_threads = []
        self.running = True
    
    def _init_data_sources(self):
        """Initialize all data source configurations"""
        return {
            'news_apis': {
                'newsapi': {
                    'url': 'https://newsapi.org/v2/everything',
                    'params': {'apiKey': self.api_keys['newsapi'], 'pageSize': 100}
                },
                'currents': {
                    'url': 'https://api.currentsapi.services/v1/latest-news',
                    'headers': {'Authorization': 'your_currents_api_key'}
                },
                'mediastack': {
                    'url': 'http://api.mediastack.com/v1/news',
                    'params': {'access_key': 'your_mediastack_key'}
                }
            },
            'financial_apis': {
                'alpha_vantage': {
                    'url': 'https://www.alphavantage.co/query',
                    'functions': ['NEWS_SENTIMENT', 'ECONOMIC_INDICATORS', 'EARNINGS']
                },
                'polygon': {
                    'url': 'https://api.polygon.io/v2',
                    'endpoints': ['tickers/news', 'reference/news']
                },
                'iex': {
                    'url': 'https://cloud.iexapis.com/stable',
                    'endpoints': ['stock/market/news', 'forex/rate']
                },
                'finnhub': {
                    'url': 'https://finnhub.io/api/v1',
                    'endpoints': ['news', 'company-news', 'economic-calendar']
                }
            },
            'crypto_apis': {
                'coinmarketcap': {
                    'url': 'https://pro-api.coinmarketcap.com/v1',
                    'endpoints': ['cryptocurrency/news', 'cryptocurrency/quotes/latest']
                },
                'coingecko': {
                    'url': 'https://api.coingecko.com/api/v3',
                    'endpoints': ['coins/markets', 'global', 'trending']
                }
            },
            'government_apis': {
                'fred': {
                    'url': 'https://api.stlouisfed.org/fred',
                    'endpoints': ['series/observations', 'releases/dates']
                },
                'sec': {
                    'url': 'https://www.sec.gov/Archives/edgar/daily-index',
                    'endpoints': ['master.idx']
                },
                'treasury': {
                    'url': 'https://api.fiscaldata.treasury.gov/services/api/v1',
                    'endpoints': ['accounting/od/rates_of_exchange']
                }
            },
            'social_apis': {
                'reddit': {
                    'url': 'https://www.reddit.com/r',
                    'subreddits': ['worldnews', 'news', 'politics', 'economics', 'cryptocurrency', 'stocks']
                },
                'youtube': {
                    'url': 'https://www.googleapis.com/youtube/v3',
                    'endpoints': ['search', 'channels']
                }
            },
            'alternative_data': {
                'google_trends': {
                    'url': 'https://trends.googleapis.com/trends/api',
                    'endpoints': ['explore']
                },
                'satellite_data': {
                    'url': 'https://api.planet.com/data/v1',
                    'endpoints': ['stats']
                }
            }
        }
    
    def _init_live_feeds_db(self):
        """Initialize live feeds database tables"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Live feeds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    data_json TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    importance_score INTEGER DEFAULT 5,
                    tags TEXT,
                    user_views INTEGER DEFAULT 0,
                    is_breaking BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # User live feed preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_live_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    feed_types TEXT,
                    keywords TEXT,
                    notification_enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Live feed subscriptions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_feed_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    feed_id INTEGER,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (feed_id) REFERENCES live_feeds (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Live feeds database tables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing live feeds database: {e}")
    
    async def fetch_news_apis(self):
        """Fetch from all news APIs"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # NewsAPI
            if self.api_keys['newsapi'] != 'your_newsapi_key':
                tasks.append(self._fetch_newsapi(session))
            
            # Add other news API tasks
            tasks.extend([
                self._fetch_currents_api(session),
                self._fetch_mediastack_api(session)
            ])
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_newsapi(self, session):
        """Fetch from NewsAPI"""
        try:
            url = self.data_sources['news_apis']['newsapi']['url']
            params = {
                'apiKey': self.api_keys['newsapi'],
                'q': 'breaking OR urgent OR market OR crypto OR politics',
                'sortBy': 'publishedAt',
                'pageSize': 50
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'source': 'NewsAPI',
                        'title': article.get('title'),
                        'content': article.get('description'),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt'),
                        'feed_type': 'news'
                    })
                
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
            return []
    
    async def _fetch_currents_api(self, session):
        """Fetch from Currents API"""
        try:
            # Placeholder for Currents API implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching Currents API: {e}")
            return []
    
    async def _fetch_mediastack_api(self, session):
        """Fetch from Mediastack API"""
        try:
            # Placeholder for Mediastack API implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching Mediastack API: {e}")
            return []
    
    async def fetch_financial_data(self):
        """Fetch from financial APIs"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_alpha_vantage(session),
                self._fetch_polygon_data(session),
                self._fetch_iex_data(session),
                self._fetch_finnhub_data(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_alpha_vantage(self, session):
        """Fetch from Alpha Vantage"""
        try:
            if self.api_keys['alpha_vantage'] == 'your_alpha_vantage_key':
                return []
            
            # News sentiment
            url = self.data_sources['financial_apis']['alpha_vantage']['url']
            params = {
                'function': 'NEWS_SENTIMENT',
                'apikey': self.api_keys['alpha_vantage'],
                'limit': 50
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                articles = []
                for item in data.get('feed', []):
                    articles.append({
                        'source': 'Alpha Vantage',
                        'title': item.get('title'),
                        'content': item.get('summary'),
                        'url': item.get('url'),
                        'published_at': item.get('time_published'),
                        'feed_type': 'financial',
                        'sentiment': item.get('overall_sentiment_label')
                    })
                
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage: {e}")
            return []
    
    async def _fetch_polygon_data(self, session):
        """Fetch from Polygon.io"""
        try:
            # Placeholder for Polygon implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching Polygon: {e}")
            return []
    
    async def _fetch_iex_data(self, session):
        """Fetch from IEX Cloud"""
        try:
            # Placeholder for IEX implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching IEX: {e}")
            return []
    
    async def _fetch_finnhub_data(self, session):
        """Fetch from Finnhub"""
        try:
            # Placeholder for Finnhub implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching Finnhub: {e}")
            return []
    
    async def fetch_crypto_data(self):
        """Fetch from crypto APIs"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_coinmarketcap(session),
                self._fetch_coingecko(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_coinmarketcap(self, session):
        """Fetch from CoinMarketCap"""
        try:
            # Placeholder for CoinMarketCap implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching CoinMarketCap: {e}")
            return []
    
    async def _fetch_coingecko(self, session):
        """Fetch from CoinGecko"""
        try:
            url = f"{self.data_sources['crypto_apis']['coingecko']['url']}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 50,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                updates = []
                for coin in data:
                    if abs(coin.get('price_change_percentage_24h', 0)) > 5:  # Significant changes
                        updates.append({
                            'source': 'CoinGecko',
                            'title': f"{coin['name']} ({coin['symbol'].upper()}) Price Update",
                            'content': f"Current price: ${coin['current_price']}, 24h change: {coin['price_change_percentage_24h']:.2f}%",
                            'feed_type': 'crypto',
                            'importance_score': 7 if abs(coin['price_change_percentage_24h']) > 10 else 5
                        })
                
                return updates
                
        except Exception as e:
            logger.error(f"Error fetching CoinGecko: {e}")
            return []
    
    async def fetch_government_data(self):
        """Fetch from government APIs"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_fred_data(session),
                self._fetch_sec_data(session),
                self._fetch_treasury_data(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_fred_data(self, session):
        """Fetch from Federal Reserve Economic Data"""
        try:
            # Placeholder for FRED implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching FRED: {e}")
            return []
    
    async def _fetch_sec_data(self, session):
        """Fetch from SEC EDGAR"""
        try:
            # Placeholder for SEC implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching SEC: {e}")
            return []
    
    async def _fetch_treasury_data(self, session):
        """Fetch from US Treasury"""
        try:
            # Placeholder for Treasury implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching Treasury: {e}")
            return []
    
    async def fetch_social_data(self):
        """Fetch from social media APIs"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_reddit_data(session),
                self._fetch_youtube_data(session)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_reddit_data(self, session):
        """Fetch from Reddit"""
        try:
            updates = []
            subreddits = self.data_sources['social_apis']['reddit']['subreddits']
            
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                params = {'limit': 10}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    for post in data['data']['children']:
                        post_data = post['data']
                        if post_data['score'] > 100:  # Popular posts only
                            updates.append({
                                'source': f'Reddit r/{subreddit}',
                                'title': post_data['title'],
                                'content': post_data.get('selftext', '')[:500],
                                'url': f"https://www.reddit.com{post_data['permalink']}",
                                'feed_type': 'social',
                                'importance_score': min(10, post_data['score'] // 100)
                            })
            
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching Reddit: {e}")
            return []
    
    async def _fetch_youtube_data(self, session):
        """Fetch from YouTube API"""
        try:
            # Placeholder for YouTube implementation
            return []
        except Exception as e:
            logger.error(f"Error fetching YouTube: {e}")
            return []
    
    def start_websocket_feeds(self):
        """Start WebSocket connections for live feeds"""
        if self.api_keys['finnhub'] != 'your_finnhub_key':
            thread = threading.Thread(target=self._run_finnhub_websocket, daemon=True)
            thread.start()
            self.websocket_threads.append(thread)
        
        # Start other WebSocket connections
        thread = threading.Thread(target=self._run_binance_websocket, daemon=True)
        thread.start()
        self.websocket_threads.append(thread)
    
    def _run_finnhub_websocket(self):
        """Run Finnhub WebSocket for stock updates"""
        try:
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get('type') == 'trade':
                        for trade in data.get('data', []):
                            self._store_live_update({
                                'source': 'Finnhub WebSocket',
                                'title': f"{trade['s']} Trade Update",
                                'content': f"Price: ${trade['p']}, Volume: {trade['v']}",
                                'feed_type': 'stock_live',
                                'data_json': json.dumps(trade),
                                'importance_score': 8
                            })
                except Exception as e:
                    logger.error(f"Error processing Finnhub message: {e}")
            
            def on_error(ws, error):
                logger.error(f"Finnhub WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                logger.info("Finnhub WebSocket connection closed")
            
            ws_url = f"wss://ws.finnhub.io?token={self.api_keys['finnhub']}"
            ws = websocket.WebSocketApp(ws_url,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Subscribe to popular stocks
            def on_open(ws):
                ws.send('{"type":"subscribe","symbol":"AAPL"}')
                ws.send('{"type":"subscribe","symbol":"TSLA"}')
                ws.send('{"type":"subscribe","symbol":"MSFT"}')
                ws.send('{"type":"subscribe","symbol":"GOOGL"}')
            
            ws.on_open = on_open
            ws.run_forever()
            
        except Exception as e:
            logger.error(f"Error in Finnhub WebSocket: {e}")
    
    def _run_binance_websocket(self):
        """Run Binance WebSocket for crypto updates"""
        try:
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if 'c' in data:  # Price data
                        price_change = float(data.get('P', 0))
                        if abs(price_change) > 1:  # Significant changes only
                            self._store_live_update({
                                'source': 'Binance WebSocket',
                                'title': f"BTC/USDT Price Alert",
                                'content': f"Current: ${data['c']}, Change: {price_change:.2f}%",
                                'feed_type': 'crypto_live',
                                'data_json': json.dumps(data),
                                'importance_score': 9 if abs(price_change) > 5 else 6
                            })
                except Exception as e:
                    logger.error(f"Error processing Binance message: {e}")
            
            def on_error(ws, error):
                logger.error(f"Binance WebSocket error: {error}")
            
            ws_url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
            ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error)
            ws.run_forever()
            
        except Exception as e:
            logger.error(f"Error in Binance WebSocket: {e}")
    
    def _store_live_update(self, update_data):
        """Store live update in database"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO live_feeds (feed_type, source, title, content, data_json, importance_score, is_breaking)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                update_data['feed_type'],
                update_data['source'],
                update_data['title'],
                update_data['content'],
                update_data.get('data_json'),
                update_data.get('importance_score', 5),
                update_data.get('importance_score', 5) >= 8
            ))
            
            conn.commit()
            conn.close()
            
            # Cache for real-time access
            with self.cache_lock:
                self.live_data_cache[update_data['feed_type']].append(update_data)
                # Keep only last 100 updates per feed type
                if len(self.live_data_cache[update_data['feed_type']]) > 100:
                    self.live_data_cache[update_data['feed_type']] = \
                        self.live_data_cache[update_data['feed_type']][-100:]
            
        except Exception as e:
            logger.error(f"Error storing live update: {e}")
    
    async def aggregate_all_sources(self):
        """Aggregate data from all sources"""
        try:
            # Fetch from all API sources
            all_tasks = [
                self.fetch_news_apis(),
                self.fetch_financial_data(),
                self.fetch_crypto_data(),
                self.fetch_government_data(),
                self.fetch_social_data()
            ]
            
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Process and store results
            total_updates = 0
            for result_group in results:
                if isinstance(result_group, list):
                    for source_results in result_group:
                        if isinstance(source_results, list):
                            for update in source_results:
                                self._store_live_update(update)
                                total_updates += 1
            
            logger.info(f"Aggregated {total_updates} updates from all sources")
            return total_updates
            
        except Exception as e:
            logger.error(f"Error in aggregate_all_sources: {e}")
            return 0
    
    def get_live_feeds(self, feed_types=None, limit=50):
        """Get recent live feeds"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            if feed_types:
                placeholders = ','.join(['?' for _ in feed_types])
                query = f'''
                    SELECT * FROM live_feeds 
                    WHERE feed_type IN ({placeholders})
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                cursor.execute(query, feed_types + [limit])
            else:
                cursor.execute('''
                    SELECT * FROM live_feeds 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            feeds = cursor.fetchall()
            conn.close()
            
            return [{
                'id': feed[0],
                'feed_type': feed[1],
                'source': feed[2],
                'title': feed[3],
                'content': feed[4],
                'data_json': feed[5],
                'timestamp': feed[6],
                'importance_score': feed[7],
                'tags': feed[8],
                'user_views': feed[9],
                'is_breaking': feed[10]
            } for feed in feeds]
            
        except Exception as e:
            logger.error(f"Error getting live feeds: {e}")
            return []
    
    def start_scheduled_aggregation(self):
        """Start scheduled data aggregation"""
        def run_aggregation():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.aggregate_all_sources())
                loop.close()
            except Exception as e:
                logger.error(f"Error in scheduled aggregation: {e}")
        
        # Schedule different intervals for different data types
        schedule.every(1).minutes.do(run_aggregation)  # Frequent updates
        
        def scheduler_loop():
            while self.running:
                schedule.run_pending()
                time.sleep(30)
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        
        logger.info("Started scheduled data aggregation")
    
    def stop(self):
        """Stop all feeds and threads"""
        self.running = False
        logger.info("Enhanced Data Aggregator stopped")

# Global instance
enhanced_aggregator = EnhancedDataAggregator()

def start_enhanced_aggregation():
    """Start the enhanced data aggregation system"""
    enhanced_aggregator.start_websocket_feeds()
    enhanced_aggregator.start_scheduled_aggregation()
    logger.info("Enhanced Data Aggregation System started")

if __name__ == "__main__":
    start_enhanced_aggregation()
