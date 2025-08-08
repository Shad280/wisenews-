"""
Scraper Protection for WiseNews
Rate limiting and anti-scraping protection for website content APIs
"""

import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify, abort
import re
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class ScraperProtection:
    def __init__(self):
        # Rate limiting configuration - User-friendly for legitimate users
        self.rate_limits = {
            'articles_per_hour': 500,      # Restored normal limits
            'requests_per_minute': 60,     # Normal browsing limits
            'requests_per_hour': 1000,     # Higher limit for active users
            'daily_limit': 5000,           # Much higher for legitimate usage
        }
        
        # Separate stricter limits for detected scrapers/bots
        self.scraper_rate_limits = {
            'articles_per_hour': 10,       # Very restrictive for bots
            'requests_per_minute': 3,      # Minimal for scrapers
            'requests_per_hour': 20,       # Low for automated tools
            'daily_limit': 50,             # Very limited for bots
        }
        
        # Suspicious patterns for bot detection
        self.suspicious_user_agents = [
            r'bot', r'crawler', r'spider', r'scraper', r'parser', r'curl', r'wget',
            r'python-requests', r'httpx', r'scrapy', r'beautifulsoup', r'selenium'
        ]
        
        # Whitelist for legitimate services (optional)
        self.whitelist_user_agents = [
            r'googlebot', r'bingbot', r'facebookexternalhit', r'twitterbot'
        ]
        
        # In-memory rate limiting cache for fast access
        self.request_cache = defaultdict(list)
        self.cache_lock = threading.Lock()
        
        # Initialize database tables
        self._init_protection_tables()
    

    def _is_likely_bot(self, user_agent: str, ip: str) -> bool:
        """Enhanced bot detection that doesn't affect regular users"""
        if not user_agent:
            return True
            
        user_agent_lower = user_agent.lower()
        
        # Check for obvious bot patterns
        for pattern in self.suspicious_user_agents:
            if re.search(pattern, user_agent_lower):
                # But allow whitelisted bots
                for whitelist_pattern in self.whitelist_user_agents:
                    if re.search(whitelist_pattern, user_agent_lower):
                        return False
                return True
        
        # Check for missing common browser indicators
        browser_indicators = ['mozilla', 'webkit', 'chrome', 'safari', 'firefox', 'edge']
        has_browser_indicator = any(indicator in user_agent_lower for indicator in browser_indicators)
        
        if not has_browser_indicator:
            return True
            
        # Check request patterns (this would need to be implemented with request tracking)
        return False
    
    def _get_rate_limits_for_request(self, user_agent: str, ip: str) -> dict:
        """Get appropriate rate limits based on bot detection"""
        if self._is_likely_bot(user_agent, ip):
            return self.scraper_rate_limits
        return self.rate_limits

    def _init_protection_tables(self):
        """Initialize anti-scraping database tables"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # IP rate limiting tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    date_hour TEXT NOT NULL,  -- Format: YYYY-MM-DD-HH
                    requests_count INTEGER DEFAULT 0,
                    articles_accessed INTEGER DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    first_request TIMESTAMP,
                    last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    UNIQUE(ip_address, date_hour)
                )
            ''')
            
            # Blocked IPs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT FALSE,
                    violation_count INTEGER DEFAULT 1
                )
            ''')
            
            # Suspicious activity log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    endpoint TEXT,
                    violation_type TEXT,
                    request_count INTEGER,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Scraper protection tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing protection tables: {e}")
    
    def check_rate_limit(self, ip_address: str, endpoint: str, user_agent: str = None) -> Tuple[bool, str]:
        """Check if IP is within rate limits"""
        try:
            # Check if IP is permanently blocked
            if self._is_ip_blocked(ip_address):
                return False, "IP address is blocked due to excessive requests"
            
            # Check if user agent is suspicious
            if self._is_suspicious_user_agent(user_agent):
                self._log_suspicious_activity(ip_address, user_agent, endpoint, "suspicious_user_agent")
                # Don't block immediately, but monitor closely
            
            # Get current time buckets
            now = datetime.now()
            current_minute = now.strftime('%Y-%m-%d-%H-%M')
            current_hour = now.strftime('%Y-%m-%d-%H')
            
            # Check minute-level rate limit (fast check with cache)
            if not self._check_minute_limit(ip_address, current_minute, user_agent):
                self._log_violation(ip_address, user_agent, endpoint, "minute_limit_exceeded")
                return False, f"Rate limit exceeded: max {self._get_rate_limits_for_request(user_agent, ip_address)['requests_per_minute']} requests per minute"
            
            # Check hour-level rate limit (database check)
            hour_allowed, hour_message = self._check_hour_limit(ip_address, current_hour, endpoint, user_agent)
            if not hour_allowed:
                self._log_violation(ip_address, user_agent, endpoint, "hour_limit_exceeded")
                return False, hour_message
            
            # Check daily limit (most important check)
            if not self._check_daily_limit(ip_address, user_agent):
                self._log_violation(ip_address, user_agent, endpoint, "daily_limit_exceeded")
                return False, f"Daily rate limit exceeded: max {self._get_rate_limits_for_request(user_agent, ip_address)['daily_limit']} requests per day"
            
            # Update request tracking
            self._update_request_tracking(ip_address, current_hour, endpoint, user_agent)
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True, "OK"  # Fail open for safety
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is currently blocked"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT blocked_until, is_permanent FROM blocked_ips 
                WHERE ip_address = ? AND (is_permanent = 1 OR blocked_until > datetime('now'))
            ''', (ip_address,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking blocked IP: {e}")
            return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent appears to be a bot/scraper"""
        if not user_agent:
            return True  # No user agent is suspicious
        
        user_agent_lower = user_agent.lower()
        
        # Check whitelist first
        for pattern in self.whitelist_user_agents:
            if re.search(pattern, user_agent_lower):
                return False
        
        # Check suspicious patterns
        for pattern in self.suspicious_user_agents:
            if re.search(pattern, user_agent_lower):
                return True
        
        return False
    
    def _check_minute_limit(self, ip_address: str, current_minute: str, user_agent: str = None) -> bool:
        """Fast minute-level rate limiting using in-memory cache"""
        with self.cache_lock:
            # Clean old entries (keep only last 2 minutes)
            cutoff_time = time.time() - 120
            for ip in list(self.request_cache.keys()):
                self.request_cache[ip] = [
                    timestamp for timestamp in self.request_cache[ip] 
                    if timestamp > cutoff_time
                ]
                if not self.request_cache[ip]:
                    del self.request_cache[ip]
            
            # Check current minute requests
            current_time = time.time()
            minute_cutoff = current_time - 60
            
            recent_requests = [
                timestamp for timestamp in self.request_cache[ip_address]
                if timestamp > minute_cutoff
            ]
            
            if len(recent_requests) >= self._get_rate_limits_for_request(user_agent, ip_address)['requests_per_minute']:
                return False
            
            # Add current request
            self.request_cache[ip_address].append(current_time)
            return True
    
    def _check_hour_limit(self, ip_address: str, current_hour: str, endpoint: str, user_agent: str) -> Tuple[bool, str]:
        """Check hourly rate limits using database"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()

            # Get current hour stats
            cursor.execute('''
                SELECT requests_count, articles_accessed FROM ip_rate_limits 
                WHERE ip_address = ? AND date_hour = ?
            ''', (ip_address, current_hour))

            result = cursor.fetchone()
            current_requests = result[0] if result else 0
            current_articles = result[1] if result else 0
            
            rate_limits = self._get_rate_limits_for_request(user_agent, ip_address)

            # Check general request limit
            if current_requests >= rate_limits['requests_per_hour']:
                conn.close()
                return False, f"🌟 Whoa there, news enthusiast! You've made {rate_limits['requests_per_hour']} requests this hour on WiseNews. ⏰ Take a short break and come back to discover more amazing stories soon!"

            # Check article-specific limit for article endpoints
            if 'article' in endpoint.lower() and current_articles >= rate_limits['articles_per_hour']:
                conn.close()
                remaining_time = 60 - datetime.now().minute
                return False, f"🌟 You've reached your hourly limit of {rate_limits['articles_per_hour']} articles on WiseNews! We keep these limits to ensure quality service for all our readers. ⏰ Please try again in about {remaining_time} minutes, or consider upgrading to WiseNews Pro for unlimited access to premium content!"

            conn.close()
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error checking hour limit: {e}")
            return True, "Error checking limits"
    
    def _check_daily_limit(self, ip_address: str, user_agent: str = None) -> bool:
        """Check daily rate limits using database"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get today's total requests for this IP
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT SUM(requests_count) FROM ip_rate_limits 
                WHERE ip_address = ? AND date_hour LIKE ?
            ''', (ip_address, f"{today}%"))
            
            result = cursor.fetchone()
            total_requests_today = result[0] if result and result[0] else 0
            
            conn.close()
            
            # Check if under daily limit
            return total_requests_today < self._get_rate_limits_for_request(user_agent, ip_address)['daily_limit']
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return True
    
    def _update_request_tracking(self, ip_address: str, current_hour: str, endpoint: str, user_agent: str):
        """Update request tracking in database"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Determine if this is an article request
            is_article_request = any(path in endpoint.lower() for path in ['article', 'news', '/api/articles'])
            
            # Insert or update hour tracking
            cursor.execute('''
                INSERT OR IGNORE INTO ip_rate_limits 
                (ip_address, date_hour, requests_count, articles_accessed, first_request, user_agent)
                VALUES (?, ?, 0, 0, datetime('now'), ?)
            ''', (ip_address, current_hour, user_agent))
            
            # Update counters
            if is_article_request:
                cursor.execute('''
                    UPDATE ip_rate_limits 
                    SET requests_count = requests_count + 1, 
                        articles_accessed = articles_accessed + 1,
                        last_request = datetime('now')
                    WHERE ip_address = ? AND date_hour = ?
                ''', (ip_address, current_hour))
            else:
                cursor.execute('''
                    UPDATE ip_rate_limits 
                    SET requests_count = requests_count + 1,
                        last_request = datetime('now')
                    WHERE ip_address = ? AND date_hour = ?
                ''', (ip_address, current_hour))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating request tracking: {e}")
    
    def _log_violation(self, ip_address: str, user_agent: str, endpoint: str, violation_type: str):
        """Log rate limit violation and potentially block IP"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get current hour to check request count
            current_hour = datetime.now().strftime('%Y-%m-%d-%H')
            cursor.execute('''
                SELECT requests_count FROM ip_rate_limits 
                WHERE ip_address = ? AND date_hour = ?
            ''', (ip_address, current_hour))
            
            result = cursor.fetchone()
            request_count = result[0] if result else 0
            
            # Log suspicious activity
            cursor.execute('''
                INSERT INTO suspicious_activity 
                (ip_address, user_agent, endpoint, violation_type, request_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip_address, user_agent, endpoint, violation_type, request_count))
            
            # Check if IP should be temporarily blocked
            if request_count > self._get_rate_limits_for_request(user_agent, ip_address)['requests_per_hour'] * 1.5:  # 150% of limit
                self._block_ip_temporarily(ip_address, f"Excessive requests: {violation_type}", hours=1)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging violation: {e}")
    
    def _log_suspicious_activity(self, ip_address: str, user_agent: str, endpoint: str, activity_type: str):
        """Log suspicious activity without blocking"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO suspicious_activity 
                (ip_address, user_agent, endpoint, violation_type, request_count)
                VALUES (?, ?, ?, ?, 0)
            ''', (ip_address, user_agent, endpoint, activity_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging suspicious activity: {e}")
    
    def _block_ip_temporarily(self, ip_address: str, reason: str, hours: int = 1):
        """Temporarily block an IP address"""
        try:
            blocked_until = datetime.now() + timedelta(hours=hours)
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO blocked_ips 
                (ip_address, reason, blocked_until, is_permanent, violation_count)
                VALUES (?, ?, ?, 0, 
                    COALESCE((SELECT violation_count + 1 FROM blocked_ips WHERE ip_address = ?), 1))
            ''', (ip_address, reason, blocked_until.isoformat(), ip_address))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"IP {ip_address} temporarily blocked for {hours} hours: {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    def get_rate_limit_stats(self) -> Dict:
        """Get current rate limiting statistics"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get current hour stats
            current_hour = datetime.now().strftime('%Y-%m-%d-%H')
            cursor.execute('''
                SELECT COUNT(*) as active_ips, 
                       SUM(requests_count) as total_requests,
                       SUM(articles_accessed) as total_articles
                FROM ip_rate_limits 
                WHERE date_hour = ?
            ''', (current_hour,))
            
            current_stats = cursor.fetchone()
            
            # Get today's total stats
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(DISTINCT ip_address) as daily_active_ips,
                       SUM(requests_count) as daily_total_requests,
                       SUM(articles_accessed) as daily_total_articles
                FROM ip_rate_limits 
                WHERE date_hour LIKE ?
            ''', (f"{today}%",))
            
            daily_stats = cursor.fetchone()
            
            # Get blocked IPs count
            cursor.execute('''
                SELECT COUNT(*) FROM blocked_ips 
                WHERE is_permanent = 1 OR blocked_until > datetime('now')
            ''', )
            
            blocked_count = cursor.fetchone()[0]
            
            # Get suspicious activity count (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM suspicious_activity 
                WHERE detected_at > datetime('now', '-1 day')
            ''', )
            
            suspicious_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'current_hour': {
                    'active_ips': current_stats[0] or 0,
                    'total_requests': current_stats[1] or 0,
                    'total_articles_accessed': current_stats[2] or 0
                },
                'daily_stats': {
                    'active_ips': daily_stats[0] or 0,
                    'total_requests': daily_stats[1] or 0,
                    'total_articles_accessed': daily_stats[2] or 0
                },
                'blocked_ips': blocked_count,
                'suspicious_activity_24h': suspicious_count,
                'rate_limits': self.rate_limits
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {
                'current_hour': {'active_ips': 0, 'total_requests': 0, 'total_articles_accessed': 0},
                'daily_stats': {'active_ips': 0, 'total_requests': 0, 'total_articles_accessed': 0},
                'blocked_ips': 0,
                'suspicious_activity_24h': 0,
                'rate_limits': self.rate_limits
            }
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip_address,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"IP {ip_address} has been unblocked")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error unblocking IP: {e}")
            return False

# Global instance
scraper_protection = ScraperProtection()

# Decorator for protecting API endpoints
def anti_scraper_protection(f):
    """Decorator to add anti-scraping protection to Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client information
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        user_agent = request.headers.get('User-Agent', '')
        endpoint = request.endpoint or request.path
        
        # Check rate limits
        allowed, message = scraper_protection.check_rate_limit(ip_address, endpoint, user_agent)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP {ip_address}: {message}")
            return jsonify({
                'error': message,  # Use the specific user-friendly message directly
                'retry_after': 3600  # seconds
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function
