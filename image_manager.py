"""
Image Manager for WiseNews
Automatically finds and adds relevant images for articles featuring events and people
"""

import requests
import json
import sqlite3
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, quote
import hashlib
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageManager:
    def __init__(self):
        # Configuration flag to disable image processing during database operations
        self.processing_enabled = True
        
        # Rate limiting configuration
        self.daily_rate_limit = 5000  # Maximum API calls per day - Generous limit
        
        # Image API configurations
        self.api_configs = {
            'unsplash': {
                'access_key': 'your_unsplash_access_key',
                'base_url': 'https://api.unsplash.com',
                'endpoints': {
                    'search': '/search/photos',
                    'random': '/photos/random'
                }
            },
            'pixabay': {
                'api_key': 'your_pixabay_api_key',
                'base_url': 'https://pixabay.com/api',
                'endpoints': {
                    'search': '/'
                }
            },
            'pexels': {
                'api_key': 'your_pexels_api_key',
                'base_url': 'https://api.pexels.com/v1',
                'endpoints': {
                    'search': '/search'
                }
            }
        }
        
        # Create images directory
        self.images_dir = 'static/images/articles'
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Initialize database tables
        self._init_image_tables()
        
        # Event and people detection patterns
        self.event_patterns = [
            r'\b(conference|summit|meeting|event|launch|announcement|ceremony|celebration)\b',
            r'\b(earnings|quarterly|annual|financial|results|report)\b',
            r'\b(merger|acquisition|deal|partnership|agreement)\b',
            r'\b(election|vote|voting|campaign|political)\b',
            r'\b(sports|game|match|tournament|championship)\b',
            r'\b(concert|festival|show|performance|entertainment)\b'
        ]
        
        self.people_patterns = [
            r'\b(CEO|President|Chairman|Director|Executive|Manager)\b',
            r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+',
            r'\b[A-Z][a-z]+\s+(said|announced|stated|declared|mentioned)\b',
            r'\b(spokesperson|representative|official|leader)\b'
        ]
        
        # Financial keywords for market-related images
        self.financial_keywords = [
            'stock market', 'trading', 'wall street', 'NYSE', 'NASDAQ',
            'bitcoin', 'cryptocurrency', 'forex', 'bonds', 'investment',
            'earnings', 'revenue', 'profit', 'loss', 'financial'
        ]
        
        # Corporate keywords for business images
        self.corporate_keywords = [
            'Apple', 'Microsoft', 'Google', 'Amazon', 'Tesla', 'Meta',
            'IBM', 'Oracle', 'Salesforce', 'Netflix', 'Uber', 'Airbnb'
        ]
    
    def _connect_db(self):
        """Connect to the database with timeout handling"""
        try:
            conn = sqlite3.connect('news_database.db', timeout=30.0)
            conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def _init_image_tables(self):
        """Initialize image-related database tables"""
        try:
            conn = self._connect_db()
            if not conn:
                logger.error("Failed to connect to database for table initialization")
                return
            cursor = conn.cursor()
            
            # Article images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    image_url TEXT NOT NULL,
                    local_path TEXT,
                    alt_text TEXT,
                    caption TEXT,
                    source TEXT,
                    source_url TEXT,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    is_primary BOOLEAN DEFAULT FALSE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    detection_type TEXT, -- event, person, corporate, generic
                    search_terms TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES news(id)
                )
            ''')
            
            # Image search cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_query TEXT NOT NULL,
                    api_source TEXT NOT NULL,
                    results_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    UNIQUE(search_query, api_source)
                )
            ''')
            
            # Rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    api_calls INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Image tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing image tables: {e}")
    
    def process_article_for_images(self, article_id: int, title: str, content: str, category: str) -> bool:
        """Process an article and add relevant images if events or people are detected"""
        try:
            # Skip processing if disabled (e.g., during bulk imports)
            if not self.processing_enabled:
                return True
                
            # Check if article already has images
            if self._article_has_images(article_id):
                logger.info(f"Article {article_id} already has images")
                return True
            
            # Analyze article content
            analysis = self._analyze_article_content(title, content, category)
            
            if not analysis['needs_images']:
                logger.info(f"Article {article_id} doesn't need images based on content analysis")
                return True
            
            # Generate search terms based on analysis
            search_terms = self._generate_image_search_terms(analysis, title, content)
            
            # Find and download images
            images_added = 0
            for search_term in search_terms[:3]:  # Limit to 3 searches per article
                image_data = self._search_for_images(search_term, analysis['detection_types'])
                
                if image_data:
                    success = self._add_image_to_article(
                        article_id, 
                        image_data, 
                        search_term, 
                        analysis['detection_types'][0] if analysis['detection_types'] else 'generic'
                    )
                    if success:
                        images_added += 1
                        break  # One good image is usually enough
            
            if images_added > 0:
                logger.info(f"Added {images_added} images to article {article_id}")
                return True
            else:
                logger.warning(f"No suitable images found for article {article_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing article {article_id} for images: {e}")
            return False
    
    def _article_has_images(self, article_id: int) -> bool:
        """Check if article already has images"""
        try:
            conn = self._connect_db()
            if not conn:
                return False
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM article_images WHERE article_id = ?
            ''', (article_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking article images: {e}")
            return False
    
    def _analyze_article_content(self, title: str, content: str, category: str) -> Dict:
        """Analyze article content to determine if images are needed and what type"""
        
        combined_text = f"{title} {content}".lower()
        analysis = {
            'needs_images': False,
            'detection_types': [],
            'confidence': 0.0,
            'key_entities': []
        }
        
        # Check for events
        event_matches = 0
        for pattern in self.event_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            event_matches += len(matches)
            if matches:
                analysis['key_entities'].extend(matches)
        
        # Check for people
        people_matches = 0
        for pattern in self.people_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            people_matches += len(matches)
            if matches:
                analysis['key_entities'].extend(matches)
        
        # Check for financial/corporate content
        financial_matches = 0
        for keyword in self.financial_keywords:
            if keyword.lower() in combined_text:
                financial_matches += 1
                analysis['key_entities'].append(keyword)
        
        corporate_matches = 0
        for keyword in self.corporate_keywords:
            if keyword.lower() in combined_text:
                corporate_matches += 1
                analysis['key_entities'].append(keyword)
        
        # Determine if images are needed
        total_matches = event_matches + people_matches + financial_matches + corporate_matches
        
        if total_matches >= 2:  # Threshold for adding images
            analysis['needs_images'] = True
            analysis['confidence'] = min(total_matches / 10.0, 1.0)  # Cap at 1.0
            
            # Determine detection types in order of priority
            if event_matches >= 2:
                analysis['detection_types'].append('event')
            if people_matches >= 1:
                analysis['detection_types'].append('person')
            if corporate_matches >= 1:
                analysis['detection_types'].append('corporate')
            if financial_matches >= 1:
                analysis['detection_types'].append('financial')
        
        # Category-based adjustments
        if category in ['business', 'finance', 'technology', 'politics']:
            analysis['needs_images'] = True
            if 'corporate' not in analysis['detection_types']:
                analysis['detection_types'].append('corporate')
        
        return analysis
    
    def _generate_image_search_terms(self, analysis: Dict, title: str, content: str) -> List[str]:
        """Generate search terms for finding relevant images"""
        
        search_terms = []
        
        # Extract key entities and create search terms
        entities = list(set(analysis['key_entities']))  # Remove duplicates
        
        for entity in entities[:5]:  # Limit to top 5 entities
            # Clean and prepare search term
            clean_entity = re.sub(r'[^\w\s]', '', entity).strip()
            if len(clean_entity) > 2:
                search_terms.append(clean_entity)
        
        # Add detection type-based terms
        for detection_type in analysis['detection_types']:
            if detection_type == 'event':
                search_terms.extend([
                    'business conference', 'corporate meeting', 'announcement event',
                    'business presentation', 'corporate event'
                ])
            elif detection_type == 'person':
                search_terms.extend([
                    'business executive', 'CEO portrait', 'corporate leader',
                    'business professional', 'executive meeting'
                ])
            elif detection_type == 'corporate':
                search_terms.extend([
                    'corporate building', 'office building', 'business headquarters',
                    'corporate logo', 'company office'
                ])
            elif detection_type == 'financial':
                search_terms.extend([
                    'stock market', 'trading floor', 'financial charts',
                    'business graph', 'market analysis'
                ])
        
        # Add generic business terms if no specific entities found
        if not search_terms:
            search_terms.extend([
                'business news', 'corporate news', 'professional meeting',
                'business handshake', 'office work'
            ])
        
        return search_terms[:10]  # Limit to 10 search terms
    
    def _search_for_images(self, search_term: str, detection_types: List[str]) -> Optional[Dict]:
        """Search for images using multiple APIs with rate limiting"""
        
        # Check rate limit first
        if not self._check_rate_limit():
            logger.warning(f"Rate limit exceeded for today. Using cached or mock data for '{search_term}'")
            # Try to get cached result first
            cached_result = self._get_cached_search(search_term)
            if cached_result:
                return cached_result
            # If no cache, return mock data
            return self._get_mock_image_data(search_term, detection_types)
        
        # Check cache first
        cached_result = self._get_cached_search(search_term)
        if cached_result:
            return cached_result
        
        # Try different APIs in order of preference
        apis_to_try = ['unsplash', 'pixabay', 'pexels']
        
        for api in apis_to_try:
            try:
                if api == 'unsplash':
                    result = self._search_unsplash(search_term, detection_types)
                elif api == 'pixabay':
                    result = self._search_pixabay(search_term, detection_types)
                elif api == 'pexels':
                    result = self._search_pexels(search_term, detection_types)
                
                if result:
                    # Increment API usage counter
                    self._increment_api_usage()
                    # Cache the result
                    self._cache_search_result(search_term, api, result)
                    return result
                    
            except Exception as e:
                logger.error(f"Error searching {api} for '{search_term}': {e}")
                continue
        
        # If no API results, return mock data for demonstration
        return self._get_mock_image_data(search_term, detection_types)
    
    def _search_unsplash(self, search_term: str, detection_types: List[str]) -> Optional[Dict]:
        """Search Unsplash for images"""
        try:
            # Mock implementation - replace with actual API calls
            """
            headers = {
                'Authorization': f'Client-ID {self.api_configs["unsplash"]["access_key"]}'
            }
            
            params = {
                'query': search_term,
                'per_page': 5,
                'orientation': 'landscape'
            }
            
            response = requests.get(
                f'{self.api_configs["unsplash"]["base_url"]}{self.api_configs["unsplash"]["endpoints"]["search"]}',
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    photo = data['results'][0]  # Take first result
                    return {
                        'url': photo['urls']['regular'],
                        'thumb_url': photo['urls']['thumb'],
                        'alt_text': photo['alt_description'] or search_term,
                        'caption': f"Photo by {photo['user']['name']} on Unsplash",
                        'source': 'Unsplash',
                        'source_url': photo['links']['html'],
                        'width': photo['width'],
                        'height': photo['height']
                    }
            """
            
            # Mock data for demonstration
            return self._get_mock_image_data(search_term, detection_types)
            
        except Exception as e:
            logger.error(f"Error in Unsplash search: {e}")
            return None
    
    def _search_pixabay(self, search_term: str, detection_types: List[str]) -> Optional[Dict]:
        """Search Pixabay for images"""
        try:
            # Mock implementation - replace with actual API calls
            return self._get_mock_image_data(search_term, detection_types)
            
        except Exception as e:
            logger.error(f"Error in Pixabay search: {e}")
            return None
    
    def _search_pexels(self, search_term: str, detection_types: List[str]) -> Optional[Dict]:
        """Search Pexels for images"""
        try:
            # Mock implementation - replace with actual API calls
            return self._get_mock_image_data(search_term, detection_types)
            
        except Exception as e:
            logger.error(f"Error in Pexels search: {e}")
            return None
    
    def _get_mock_image_data(self, search_term: str, detection_types: List[str]) -> Dict:
        """Generate mock image data for demonstration"""
        
        # Generate different mock images based on detection type
        base_urls = {
            'event': 'https://images.unsplash.com/photo-1591115765373-5207764f72e7?w=800',  # Business conference
            'person': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800',  # Business person
            'corporate': 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800',  # Office building
            'financial': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800',  # Stock charts
            'generic': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800'  # Generic business
        }
        
        # Choose appropriate image based on detection types
        image_type = detection_types[0] if detection_types else 'generic'
        image_url = base_urls.get(image_type, base_urls['generic'])
        
        return {
            'url': image_url,
            'thumb_url': image_url.replace('w=800', 'w=300'),
            'alt_text': f"{search_term} - {image_type} related image",
            'caption': f"Stock photo related to {search_term}",
            'source': 'Stock Photo',
            'source_url': image_url,
            'width': 800,
            'height': 600
        }
    
    def _add_image_to_article(self, article_id: int, image_data: Dict, search_term: str, detection_type: str) -> bool:
        """Add image to article in database and optionally download locally"""
        try:
            conn = self._connect_db()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            cursor = conn.cursor()
            
            # Download and save image locally (optional)
            local_path = None
            file_size = None
            
            try:
                local_path, file_size = self._download_image(image_data['url'], article_id, search_term)
            except Exception as e:
                logger.warning(f"Failed to download image locally: {e}")
            
            # Insert image record
            cursor.execute('''
                INSERT INTO article_images 
                (article_id, image_url, local_path, alt_text, caption, source, source_url, 
                 width, height, file_size, is_primary, detection_type, search_terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id,
                image_data['url'],
                local_path,
                image_data['alt_text'],
                image_data['caption'],
                image_data['source'],
                image_data['source_url'],
                image_data.get('width'),
                image_data.get('height'),
                file_size,
                True,  # Mark as primary image
                detection_type,
                search_term
            ))
            
            # Update the news table to include the image URL
            cursor.execute('''
                UPDATE news 
                SET image_url = ? 
                WHERE id = ? AND (image_url IS NULL OR image_url = '')
            ''', (local_path or image_data['url'], article_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added image to article {article_id}: {image_data['url']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image to article {article_id}: {e}")
            return False
    
    def _download_image(self, url: str, article_id: int, search_term: str) -> Tuple[str, int]:
        """Download image locally and return path and file size"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_search_term = re.sub(r'[^\w\s-]', '', search_term)[:20]
            filename = f"article_{article_id}_{safe_search_term}_{url_hash}.jpg"
            local_path = os.path.join(self.images_dir, filename)
            
            # Process and save image
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if too large
            if img.width > 1200 or img.height > 800:
                img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save image
            img.save(local_path, 'JPEG', quality=85, optimize=True)
            
            file_size = os.path.getsize(local_path)
            
            # Return relative path for web serving
            relative_path = f"/static/images/articles/{filename}"
            
            return relative_path, file_size
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            raise
    
    def _get_cached_search(self, search_term: str) -> Optional[Dict]:
        """Get cached search results"""
        try:
            conn = self._connect_db()
            if not conn:
                return None
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT results_json FROM image_search_cache 
                WHERE search_query = ? 
                AND expires_at > datetime('now')
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (search_term,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached search: {e}")
            return None
    
    def _cache_search_result(self, search_term: str, api_source: str, result: Dict):
        """Cache search results"""
        try:
            conn = self._connect_db()
            if not conn:
                return
            cursor = conn.cursor()
            
            expires_at = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO image_search_cache 
                (search_query, api_source, results_json, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (search_term, api_source, json.dumps(result), expires_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error caching search result: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within the daily rate limit"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT api_calls FROM image_api_usage WHERE date = ?
            ''', (today,))
            
            result = cursor.fetchone()
            conn.close()
            
            current_calls = result[0] if result else 0
            
            return current_calls < self.daily_rate_limit
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False  # Err on the side of caution
    
    def _increment_api_usage(self):
        """Increment the daily API usage counter"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO image_api_usage (date, api_calls) VALUES (?, 0)
            ''', (today,))
            
            cursor.execute('''
                UPDATE image_api_usage SET api_calls = api_calls + 1 WHERE date = ?
            ''', (today,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error incrementing API usage: {e}")
    
    def get_daily_usage_stats(self) -> Dict:
        """Get current daily usage statistics"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT api_calls FROM image_api_usage WHERE date = ?
            ''', (today,))
            
            result = cursor.fetchone()
            current_calls = result[0] if result else 0
            
            # Get last 7 days of usage
            cursor.execute('''
                SELECT date, api_calls FROM image_api_usage 
                WHERE date >= date('now', '-7 days')
                ORDER BY date DESC
            ''', )
            
            recent_usage = cursor.fetchall()
            conn.close()
            
            return {
                'current_calls': current_calls,
                'daily_limit': self.daily_rate_limit,
                'remaining_calls': max(0, self.daily_rate_limit - current_calls),
                'usage_percentage': (current_calls / self.daily_rate_limit) * 100,
                'recent_usage': recent_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {
                'current_calls': 0,
                'daily_limit': self.daily_rate_limit,
                'remaining_calls': self.daily_rate_limit,
                'usage_percentage': 0,
                'recent_usage': []
            }
    
    def get_article_images(self, article_id: int) -> List[Dict]:
        """Get all images for an article"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, image_url, local_path, alt_text, caption, source, 
                       source_url, width, height, is_primary, detection_type
                FROM article_images 
                WHERE article_id = ?
                ORDER BY is_primary DESC, created_at ASC
            ''', (article_id,))
            
            images = []
            for row in cursor.fetchall():
                images.append({
                    'id': row[0],
                    'url': row[2] or row[1],  # Prefer local path
                    'original_url': row[1],
                    'alt_text': row[3],
                    'caption': row[4],
                    'source': row[5],
                    'source_url': row[6],
                    'width': row[7],
                    'height': row[8],
                    'is_primary': row[9],
                    'detection_type': row[10]
                })
            
            conn.close()
            return images
            
        except Exception as e:
            logger.error(f"Error getting article images: {e}")
            return []
    
    def cleanup_orphaned_images(self):
        """Clean up images for deleted articles"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Find orphaned images
            cursor.execute('''
                SELECT ai.id, ai.local_path 
                FROM article_images ai
                LEFT JOIN news n ON ai.article_id = n.id
                WHERE n.id IS NULL
            ''')
            
            orphaned_images = cursor.fetchall()
            
            for image_id, local_path in orphaned_images:
                # Delete local file if it exists
                if local_path and os.path.exists(local_path.lstrip('/')):
                    try:
                        os.remove(local_path.lstrip('/'))
                    except Exception as e:
                        logger.warning(f"Failed to delete local image file: {e}")
                
                # Delete database record
                cursor.execute('DELETE FROM article_images WHERE id = ?', (image_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {len(orphaned_images)} orphaned images")
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned images: {e}")
    
    def bulk_process_articles_for_images(self, limit: int = 50):
        """Process multiple articles for images in bulk with rate limiting"""
        try:
            # Check current usage before starting
            usage_stats = self.get_daily_usage_stats()
            if usage_stats['remaining_calls'] <= 0:
                logger.warning("Daily API rate limit reached. Cannot process more articles today.")
                return 0
            
            # Adjust limit based on remaining API calls
            max_processable = min(limit, usage_stats['remaining_calls'])
            logger.info(f"Processing up to {max_processable} articles (Rate limit: {usage_stats['remaining_calls']} calls remaining)")
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get articles without images
            cursor.execute('''
                SELECT n.id, n.title, n.content, n.category
                FROM news n
                LEFT JOIN article_images ai ON n.id = ai.article_id
                WHERE ai.id IS NULL
                AND n.published_date > datetime('now', '-30 days')
                ORDER BY n.published_date DESC
                LIMIT ?
            ''', (max_processable,))
            
            articles = cursor.fetchall()
            conn.close()
            
            processed = 0
            for article_id, title, content, category in articles:
                try:
                    # Check rate limit before each article
                    if not self._check_rate_limit():
                        logger.warning(f"Rate limit reached after processing {processed} articles")
                        break
                    
                    success = self.process_article_for_images(article_id, title, content, category)
                    if success:
                        processed += 1
                    
                    # Small delay to avoid hitting API rate limits
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing article {article_id}: {e}")
                    continue
            
            # Log final statistics
            final_stats = self.get_daily_usage_stats()
            logger.info(f"Bulk processed {processed} articles for images. API calls used: {final_stats['current_calls']}/{final_stats['daily_limit']}")
            return processed
            
        except Exception as e:
            logger.error(f"Error in bulk processing: {e}")
            return 0

# Global instance for use throughout the application
image_manager = ImageManager()
# Temporarily disable image processing during bulk operations to prevent database locks
image_manager.processing_enabled = False
