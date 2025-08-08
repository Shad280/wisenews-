"""
Social Media Manager for WiseNews
Handles automated posting, user authentication, content sharing, and social monitoring
"""

import requests
import json
import sqlite3
import logging
import time
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode, quote
import secrets

logger = logging.getLogger(__name__)

class SocialMediaManager:
    def __init__(self):
        # Social media API configurations
        self.api_configs = {
            'twitter': {
                'api_key': 'your_twitter_api_key',
                'api_secret': 'your_twitter_api_secret',
                'access_token': 'your_twitter_access_token',
                'access_token_secret': 'your_twitter_access_token_secret',
                'bearer_token': 'your_twitter_bearer_token',
                'base_url': 'https://api.twitter.com/2',
                'upload_url': 'https://upload.twitter.com/1.1'
            },
            'facebook': {
                'app_id': 'your_facebook_app_id',
                'app_secret': 'your_facebook_app_secret',
                'access_token': 'your_facebook_page_access_token',
                'page_id': 'your_facebook_page_id',
                'base_url': 'https://graph.facebook.com/v18.0'
            },
            'linkedin': {
                'client_id': 'your_linkedin_client_id',
                'client_secret': 'your_linkedin_client_secret',
                'access_token': 'your_linkedin_access_token',
                'organization_id': 'your_linkedin_organization_id',
                'base_url': 'https://api.linkedin.com/v2'
            },
            'instagram': {
                'access_token': 'your_instagram_access_token',
                'business_account_id': 'your_instagram_business_account_id',
                'base_url': 'https://graph.facebook.com/v18.0'
            }
        }
        
        # Initialize database tables
        self._init_social_tables()
    
    def _init_social_tables(self):
        """Initialize social media related database tables"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Social media posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_media_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    platform TEXT NOT NULL,
                    post_id TEXT,
                    content TEXT NOT NULL,
                    image_url TEXT,
                    scheduled_time TIMESTAMP,
                    posted_time TIMESTAMP,
                    status TEXT DEFAULT 'pending', -- pending, posted, failed
                    engagement_data TEXT, -- JSON data for likes, shares, comments
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES news(id)
                )
            ''')
            
            # User social accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_social_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    social_user_id TEXT NOT NULL,
                    username TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    profile_data TEXT, -- JSON data
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, platform)
                )
            ''')
            
            # Social media analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_media_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    metric_name TEXT NOT NULL, -- likes, shares, comments, reach, impressions
                    metric_value INTEGER NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES social_media_posts(id)
                )
            ''')
            
            # Social media content queue table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_content_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL, -- news_article, breaking_news, market_update
                    reference_id INTEGER, -- article_id or event_id
                    platforms TEXT NOT NULL, -- JSON array of platforms
                    content TEXT NOT NULL,
                    image_url TEXT,
                    hashtags TEXT,
                    priority INTEGER DEFAULT 1, -- 1=low, 2=medium, 3=high, 4=urgent
                    scheduled_time TIMESTAMP,
                    status TEXT DEFAULT 'queued', -- queued, processing, posted, failed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Social media trends table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_media_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    trend_name TEXT NOT NULL,
                    trend_volume INTEGER,
                    trend_category TEXT,
                    location TEXT DEFAULT 'global',
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    relevance_score REAL DEFAULT 0.0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Social media tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing social media tables: {e}")
    
    def auto_post_breaking_news(self, article_data: Dict, platforms: List[str] = None) -> bool:
        """Automatically post breaking news to social media platforms"""
        try:
            if platforms is None:
                platforms = ['twitter', 'linkedin']  # Default platforms for news
            
            # Create social media content
            content = self._create_social_content(article_data, 'breaking_news')
            
            success_count = 0
            for platform in platforms:
                try:
                    if platform == 'twitter':
                        result = self._post_to_twitter(content)
                    elif platform == 'facebook':
                        result = self._post_to_facebook(content)
                    elif platform == 'linkedin':
                        result = self._post_to_linkedin(content)
                    elif platform == 'instagram':
                        result = self._post_to_instagram(content)
                    else:
                        logger.warning(f"Unsupported platform: {platform}")
                        continue
                    
                    if result:
                        success_count += 1
                        self._store_social_post(article_data.get('id'), platform, content, result)
                        logger.info(f"Successfully posted to {platform}")
                    
                except Exception as e:
                    logger.error(f"Error posting to {platform}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in auto_post_breaking_news: {e}")
            return False
    
    def _create_social_content(self, article_data: Dict, content_type: str) -> Dict:
        """Create optimized content for social media platforms"""
        
        title = article_data.get('title', '')
        category = article_data.get('category', '')
        url = article_data.get('url', '')
        
        # Generate hashtags based on category
        hashtags = self._generate_hashtags(category, article_data)
        
        # Create platform-specific content
        content = {
            'twitter': {
                'text': self._create_twitter_text(title, hashtags, url),
                'hashtags': hashtags[:5],  # Twitter limit
                'url': url
            },
            'facebook': {
                'message': self._create_facebook_text(title, article_data),
                'link': url,
                'hashtags': hashtags
            },
            'linkedin': {
                'text': self._create_linkedin_text(title, article_data),
                'url': url,
                'hashtags': hashtags[:3]  # LinkedIn best practice
            },
            'instagram': {
                'caption': self._create_instagram_caption(title, hashtags),
                'hashtags': hashtags[:30],  # Instagram limit
                'image_required': True
            }
        }
        
        return content
    
    def _create_twitter_text(self, title: str, hashtags: List[str], url: str) -> str:
        """Create Twitter-optimized text (280 character limit)"""
        
        # Reserve space for hashtags and URL
        hashtag_text = ' '.join(f'#{tag}' for tag in hashtags[:3])
        url_length = 23  # Twitter's URL shortening length
        
        max_title_length = 280 - len(hashtag_text) - url_length - 10  # Buffer
        
        if len(title) > max_title_length:
            title = title[:max_title_length-3] + '...'
        
        # Add urgency indicators for breaking news
        if any(word in title.lower() for word in ['breaking', 'urgent', 'alert']):
            emoji = '🚨 '
        elif any(word in title.lower() for word in ['market', 'stock', 'trading']):
            emoji = '📈 '
        elif any(word in title.lower() for word in ['earnings', 'financial']):
            emoji = '💰 '
        else:
            emoji = '📰 '
        
        return f"{emoji}{title}\n\n{hashtag_text}\n\n{url}"
    
    def _create_facebook_text(self, title: str, article_data: Dict) -> str:
        """Create Facebook-optimized text"""
        
        content = article_data.get('content', '')
        summary = content[:200] + '...' if len(content) > 200 else content
        
        facebook_text = f"""🔥 BREAKING NEWS UPDATE
        
{title}

{summary}

Stay informed with WiseNews - your trusted source for real-time market intelligence and breaking news coverage.

#WiseNews #BreakingNews #MarketNews #FinancialNews"""
        
        return facebook_text
    
    def _create_linkedin_text(self, title: str, article_data: Dict) -> str:
        """Create LinkedIn-optimized professional content"""
        
        category = article_data.get('category', '')
        
        linkedin_text = f"""📊 MARKET INTELLIGENCE UPDATE

{title}

This development has significant implications for:
• Market participants and investors
• Industry stakeholders and analysts  
• Financial planning and strategy

Our team continues to monitor this story and provide comprehensive analysis for informed decision-making.

Follow WiseNews for institutional-grade market intelligence and real-time updates on developments that matter to your business.

#MarketIntelligence #BusinessNews #FinancialAnalysis #InvestmentInsights"""
        
        return linkedin_text
    
    def _create_instagram_caption(self, title: str, hashtags: List[str]) -> str:
        """Create Instagram-optimized caption"""
        
        caption = f"""📱 MARKET UPDATE ALERT

{title}

Swipe for key insights and analysis 👉

Stay ahead of market movements with WiseNews 📈

{' '.join(f'#{tag}' for tag in hashtags[:25])}

#WiseNews #MarketUpdate #BusinessNews #Investing #Finance"""
        
        return caption
    
    def _generate_hashtags(self, category: str, article_data: Dict) -> List[str]:
        """Generate relevant hashtags based on content"""
        
        base_hashtags = ['WiseNews', 'BreakingNews', 'MarketNews']
        
        category_hashtags = {
            'business': ['Business', 'Economy', 'Corporate', 'Markets'],
            'technology': ['Technology', 'Tech', 'Innovation', 'Digital'],
            'finance': ['Finance', 'Markets', 'Trading', 'Investment', 'Stocks'],
            'politics': ['Politics', 'Policy', 'Government', 'Regulation'],
            'sports': ['Sports', 'Athletics', 'Competition'],
            'entertainment': ['Entertainment', 'Media', 'Culture'],
            'health': ['Health', 'Healthcare', 'Medical', 'Wellness'],
            'science': ['Science', 'Research', 'Innovation', 'Discovery']
        }
        
        hashtags = base_hashtags[:]
        
        # Add category-specific hashtags
        if category.lower() in category_hashtags:
            hashtags.extend(category_hashtags[category.lower()])
        
        # Add content-specific hashtags
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        keyword_hashtags = {
            'earnings': ['Earnings', 'EPS', 'Revenue', 'Quarterly'],
            'fed': ['FederalReserve', 'Fed', 'InterestRates', 'MonetaryPolicy'],
            'sec': ['SEC', 'Regulation', 'Compliance', 'Enforcement'],
            'merger': ['Merger', 'Acquisition', 'MA', 'Corporate'],
            'ipo': ['IPO', 'PublicOffering', 'Listing'],
            'crypto': ['Crypto', 'Bitcoin', 'Blockchain', 'Digital'],
            'oil': ['Oil', 'Energy', 'Petroleum', 'OPEC'],
            'gold': ['Gold', 'PreciousMetals', 'Commodities']
        }
        
        for keyword, tags in keyword_hashtags.items():
            if keyword in title or keyword in content:
                hashtags.extend(tags[:2])  # Limit to avoid spam
        
        # Remove duplicates and return
        return list(dict.fromkeys(hashtags))[:20]  # Limit to 20 hashtags
    
    def _post_to_twitter(self, content: Dict) -> Optional[Dict]:
        """Post content to Twitter/X"""
        try:
            # This is a mock implementation - replace with actual Twitter API calls
            twitter_content = content.get('twitter', {})
            
            # In production, you would use the Twitter API v2
            # Example API call structure:
            """
            headers = {
                'Authorization': f'Bearer {self.api_configs["twitter"]["bearer_token"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': twitter_content['text']
            }
            
            response = requests.post(
                f'{self.api_configs["twitter"]["base_url"]}/tweets',
                headers=headers,
                json=payload
            )
            """
            
            # Mock response for demonstration
            mock_response = {
                'post_id': f'twitter_{int(time.time())}',
                'platform': 'twitter',
                'status': 'posted',
                'engagement': {'likes': 0, 'retweets': 0, 'replies': 0}
            }
            
            logger.info(f"Posted to Twitter: {twitter_content['text'][:50]}...")
            return mock_response
            
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return None
    
    def _post_to_facebook(self, content: Dict) -> Optional[Dict]:
        """Post content to Facebook"""
        try:
            # Mock implementation - replace with actual Facebook Graph API calls
            facebook_content = content.get('facebook', {})
            
            # In production, you would use Facebook Graph API
            """
            url = f"{self.api_configs['facebook']['base_url']}/{self.api_configs['facebook']['page_id']}/feed"
            
            params = {
                'message': facebook_content['message'],
                'link': facebook_content.get('link'),
                'access_token': self.api_configs['facebook']['access_token']
            }
            
            response = requests.post(url, data=params)
            """
            
            mock_response = {
                'post_id': f'facebook_{int(time.time())}',
                'platform': 'facebook',
                'status': 'posted',
                'engagement': {'likes': 0, 'shares': 0, 'comments': 0}
            }
            
            logger.info(f"Posted to Facebook: {facebook_content['message'][:50]}...")
            return mock_response
            
        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            return None
    
    def _post_to_linkedin(self, content: Dict) -> Optional[Dict]:
        """Post content to LinkedIn"""
        try:
            # Mock implementation - replace with actual LinkedIn API calls
            linkedin_content = content.get('linkedin', {})
            
            # In production, you would use LinkedIn API v2
            """
            headers = {
                'Authorization': f'Bearer {self.api_configs["linkedin"]["access_token"]}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            payload = {
                'author': f'urn:li:organization:{self.api_configs["linkedin"]["organization_id"]}',
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': linkedin_content['text']
                        },
                        'shareMediaCategory': 'ARTICLE',
                        'media': [{
                            'status': 'READY',
                            'originalUrl': linkedin_content['url']
                        }]
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }
            
            response = requests.post(
                f'{self.api_configs["linkedin"]["base_url"]}/ugcPosts',
                headers=headers,
                json=payload
            )
            """
            
            mock_response = {
                'post_id': f'linkedin_{int(time.time())}',
                'platform': 'linkedin',
                'status': 'posted',
                'engagement': {'likes': 0, 'shares': 0, 'comments': 0}
            }
            
            logger.info(f"Posted to LinkedIn: {linkedin_content['text'][:50]}...")
            return mock_response
            
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return None
    
    def _post_to_instagram(self, content: Dict) -> Optional[Dict]:
        """Post content to Instagram (requires image)"""
        try:
            # Instagram requires images, so this would need image generation
            instagram_content = content.get('instagram', {})
            
            if not instagram_content.get('image_required'):
                logger.warning("Instagram post requires image")
                return None
            
            # Mock response for demonstration
            mock_response = {
                'post_id': f'instagram_{int(time.time())}',
                'platform': 'instagram',
                'status': 'posted',
                'engagement': {'likes': 0, 'comments': 0}
            }
            
            logger.info(f"Posted to Instagram: {instagram_content['caption'][:50]}...")
            return mock_response
            
        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            return None
    
    def _store_social_post(self, article_id: int, platform: str, content: Dict, result: Dict):
        """Store social media post information in database"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            platform_content = content.get(platform, {})
            
            cursor.execute('''
                INSERT INTO social_media_posts 
                (article_id, platform, post_id, content, posted_time, status, engagement_data)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            ''', (
                article_id,
                platform,
                result.get('post_id'),
                json.dumps(platform_content),
                result.get('status', 'posted'),
                json.dumps(result.get('engagement', {}))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing social post: {e}")
    
    def queue_content_for_posting(self, content_data: Dict, platforms: List[str], 
                                 priority: int = 1, scheduled_time: datetime = None):
        """Queue content for scheduled posting"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            content = self._create_social_content(content_data, 'scheduled')
            
            cursor.execute('''
                INSERT INTO social_content_queue 
                (content_type, reference_id, platforms, content, priority, scheduled_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                content_data.get('type', 'article'),
                content_data.get('id'),
                json.dumps(platforms),
                json.dumps(content),
                priority,
                scheduled_time.isoformat() if scheduled_time else None
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Queued content for posting to {', '.join(platforms)}")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing content: {e}")
            return False
    
    def process_content_queue(self):
        """Process queued content for posting"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get queued content ready for posting
            cursor.execute('''
                SELECT id, content_type, reference_id, platforms, content, priority
                FROM social_content_queue 
                WHERE status = 'queued' 
                AND (scheduled_time IS NULL OR scheduled_time <= CURRENT_TIMESTAMP)
                ORDER BY priority DESC, created_at ASC
                LIMIT 10
            ''')
            
            queue_items = cursor.fetchall()
            
            for item in queue_items:
                queue_id, content_type, reference_id, platforms_json, content_json, priority = item
                
                try:
                    platforms = json.loads(platforms_json)
                    content = json.loads(content_json)
                    
                    # Update status to processing
                    cursor.execute('''
                        UPDATE social_content_queue 
                        SET status = 'processing' 
                        WHERE id = ?
                    ''', (queue_id,))
                    conn.commit()
                    
                    # Post to each platform
                    success = False
                    for platform in platforms:
                        if platform == 'twitter':
                            result = self._post_to_twitter(content)
                        elif platform == 'facebook':
                            result = self._post_to_facebook(content)
                        elif platform == 'linkedin':
                            result = self._post_to_linkedin(content)
                        elif platform == 'instagram':
                            result = self._post_to_instagram(content)
                        
                        if result:
                            success = True
                            self._store_social_post(reference_id, platform, content, result)
                    
                    # Update queue status
                    final_status = 'posted' if success else 'failed'
                    cursor.execute('''
                        UPDATE social_content_queue 
                        SET status = ? 
                        WHERE id = ?
                    ''', (final_status, queue_id))
                    conn.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_id}: {e}")
                    cursor.execute('''
                        UPDATE social_content_queue 
                        SET status = 'failed' 
                        WHERE id = ?
                    ''', (queue_id,))
                    conn.commit()
            
            conn.close()
            logger.info(f"Processed {len(queue_items)} queue items")
            
        except Exception as e:
            logger.error(f"Error processing content queue: {e}")
    
    def create_oauth_url(self, platform: str, user_id: int, redirect_uri: str) -> str:
        """Create OAuth URL for social media authentication"""
        
        state = self._generate_oauth_state(user_id, platform)
        
        oauth_urls = {
            'twitter': f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={self.api_configs['twitter']['api_key']}&redirect_uri={quote(redirect_uri)}&scope=tweet.read%20tweet.write%20users.read&state={state}",
            'facebook': f"https://www.facebook.com/v18.0/dialog/oauth?client_id={self.api_configs['facebook']['app_id']}&redirect_uri={quote(redirect_uri)}&state={state}&scope=pages_manage_posts,pages_read_engagement",
            'linkedin': f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={self.api_configs['linkedin']['client_id']}&redirect_uri={quote(redirect_uri)}&state={state}&scope=w_member_social,r_liteprofile",
            'google': f"https://accounts.google.com/oauth2/auth?response_type=code&client_id=your_google_client_id&redirect_uri={quote(redirect_uri)}&scope=profile%20email&state={state}"
        }
        
        return oauth_urls.get(platform, '')
    
    def _generate_oauth_state(self, user_id: int, platform: str) -> str:
        """Generate secure OAuth state parameter"""
        state_data = f"{user_id}:{platform}:{int(time.time())}"
        return base64.urlsafe_b64encode(state_data.encode()).decode()
    
    def handle_oauth_callback(self, platform: str, code: str, state: str) -> bool:
        """Handle OAuth callback and store user tokens"""
        try:
            # Decode state to get user_id
            state_data = base64.urlsafe_b64decode(state.encode()).decode()
            user_id, platform_check, timestamp = state_data.split(':')
            
            if platform != platform_check:
                logger.error("Platform mismatch in OAuth callback")
                return False
            
            # Exchange code for access token (mock implementation)
            # In production, make actual API calls to exchange the code
            access_token = f"mock_token_{platform}_{user_id}_{int(time.time())}"
            
            # Store user social account
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_social_accounts 
                (user_id, platform, social_user_id, access_token, is_active, updated_at)
                VALUES (?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP)
            ''', (user_id, platform, f"{platform}_user_{user_id}", access_token))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully connected {platform} account for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return False
    
    def get_social_analytics(self, days: int = 30) -> Dict:
        """Get social media analytics for the specified period"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get post performance by platform
            cursor.execute('''
                SELECT 
                    platform,
                    COUNT(*) as total_posts,
                    AVG(CAST(JSON_EXTRACT(engagement_data, '$.likes') AS INTEGER)) as avg_likes,
                    AVG(CAST(JSON_EXTRACT(engagement_data, '$.shares') AS INTEGER)) as avg_shares,
                    AVG(CAST(JSON_EXTRACT(engagement_data, '$.comments') AS INTEGER)) as avg_comments
                FROM social_media_posts 
                WHERE posted_time > datetime('now', '-{} days')
                AND status = 'posted'
                GROUP BY platform
            '''.format(days))
            
            platform_stats = {}
            for row in cursor.fetchall():
                platform, total_posts, avg_likes, avg_shares, avg_comments = row
                platform_stats[platform] = {
                    'total_posts': total_posts,
                    'avg_engagement': {
                        'likes': avg_likes or 0,
                        'shares': avg_shares or 0,
                        'comments': avg_comments or 0
                    }
                }
            
            # Get top performing posts
            cursor.execute('''
                SELECT platform, content, engagement_data, posted_time
                FROM social_media_posts 
                WHERE posted_time > datetime('now', '-{} days')
                AND status = 'posted'
                ORDER BY (
                    CAST(JSON_EXTRACT(engagement_data, '$.likes') AS INTEGER) +
                    CAST(JSON_EXTRACT(engagement_data, '$.shares') AS INTEGER) * 2 +
                    CAST(JSON_EXTRACT(engagement_data, '$.comments') AS INTEGER) * 3
                ) DESC
                LIMIT 10
            '''.format(days))
            
            top_posts = []
            for row in cursor.fetchall():
                platform, content, engagement_data, posted_time = row
                top_posts.append({
                    'platform': platform,
                    'content': json.loads(content) if content else {},
                    'engagement': json.loads(engagement_data) if engagement_data else {},
                    'posted_time': posted_time
                })
            
            conn.close()
            
            return {
                'platform_stats': platform_stats,
                'top_posts': top_posts,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting social analytics: {e}")
            return {}
    
    def monitor_social_trends(self) -> List[Dict]:
        """Monitor social media trends relevant to news and finance"""
        try:
            # This would integrate with Twitter API, Google Trends, etc.
            # Mock implementation for demonstration
            mock_trends = [
                {
                    'platform': 'twitter',
                    'trend': '#MarketUpdate',
                    'volume': 15420,
                    'category': 'finance',
                    'relevance_score': 0.85
                },
                {
                    'platform': 'twitter',
                    'trend': '#BreakingNews',
                    'volume': 23100,
                    'category': 'news',
                    'relevance_score': 0.92
                },
                {
                    'platform': 'linkedin',
                    'trend': 'Quarterly Earnings',
                    'volume': 8900,
                    'category': 'business',
                    'relevance_score': 0.78
                }
            ]
            
            # Store trends in database
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            for trend in mock_trends:
                cursor.execute('''
                    INSERT INTO social_media_trends 
                    (platform, trend_name, trend_volume, trend_category, relevance_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    trend['platform'],
                    trend['trend'],
                    trend['volume'],
                    trend['category'],
                    trend['relevance_score']
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Monitored {len(mock_trends)} social media trends")
            return mock_trends
            
        except Exception as e:
            logger.error(f"Error monitoring social trends: {e}")
            return []

# Global instance for use throughout the application
social_media_manager = SocialMediaManager()
