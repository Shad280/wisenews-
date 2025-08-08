# WiseNews API Key Management System

import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, abort

class APIKeyManager:
    def __init__(self, db_path='news_database.db'):
        self.db_path = db_path
        self.init_api_tables()
    
    def init_api_tables(self):
        """Initialize API key management tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                api_secret TEXT NOT NULL,
                email TEXT NOT NULL,
                organization TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                approved_at DATETIME,
                last_used DATETIME,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 100,
                notes TEXT
            )
        ''')
        
        # API Usage logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_status INTEGER,
                FOREIGN KEY (api_key) REFERENCES api_keys (api_key)
            )
        ''')
        
        # Blocked IPs/User Agents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                user_agent TEXT,
                reason TEXT NOT NULL,
                blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                auto_block BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Rate limiting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT,
                ip_address TEXT,
                requests_count INTEGER DEFAULT 1,
                window_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(api_key, ip_address)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_api_key(self, email, organization, key_name):
        """Generate new API key for approval"""
        api_key = f"wn_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(48)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys (key_name, api_key, api_secret, email, organization)
            VALUES (?, ?, ?, ?, ?)
        ''', (key_name, api_key, api_secret, email, organization))
        
        conn.commit()
        conn.close()
        
        return {
            'api_key': api_key,
            'status': 'pending_approval',
            'message': 'API key generated. Awaiting admin approval.'
        }
    
    def approve_api_key(self, api_key, rate_limit=100):
        """Approve pending API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE api_keys 
            SET status = 'active', approved_at = CURRENT_TIMESTAMP, rate_limit = ?
            WHERE api_key = ? AND status = 'pending'
        ''', (rate_limit, api_key))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def get_user_keys(self, email):
        """Get all API keys for a user by email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT key_name, api_key, status, created_at, last_used, usage_count, rate_limit
                FROM api_keys 
                WHERE email = ?
                ORDER BY created_at DESC
            ''', (email,))
            
            keys = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            return [{
                'key_name': key[0],
                'api_key': key[1],
                'status': key[2],
                'created_at': key[3],
                'last_used': key[4],
                'usage_count': key[5] or 0,
                'rate_limit': key[6] or 100
            } for key in keys]
            
        except Exception as e:
            print(f"Error getting user keys: {e}")
            return []
    
    def validate_api_key(self, api_key):
        """Validate API key and check status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, rate_limit, usage_count 
            FROM api_keys 
            WHERE api_key = ?
        ''', (api_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'active':
            return True, result[1], result[2]  # status, rate_limit, usage_count
        
        return False, 0, 0
    
    def log_api_usage(self, api_key, endpoint, ip_address, user_agent, status):
        """Log API usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log usage
        cursor.execute('''
            INSERT INTO api_usage (api_key, endpoint, ip_address, user_agent, response_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (api_key, endpoint, ip_address, user_agent, status))
        
        # Update usage count and last used
        cursor.execute('''
            UPDATE api_keys 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE api_key = ?
        ''', (api_key,))
        
        conn.commit()
        conn.close()
    
    def check_rate_limit(self, api_key, ip_address, rate_limit):
        """Check if API key/IP is within rate limits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean old rate limit entries (older than 1 hour)
        cursor.execute('''
            DELETE FROM rate_limits 
            WHERE window_start < datetime('now', '-1 hour')
        ''')
        
        # Check current rate limit
        cursor.execute('''
            SELECT requests_count FROM rate_limits 
            WHERE api_key = ? AND ip_address = ?
        ''', (api_key, ip_address))
        
        result = cursor.fetchone()
        
        if result:
            if result[0] >= rate_limit:
                conn.close()
                return False  # Rate limit exceeded
            
            # Increment counter
            cursor.execute('''
                UPDATE rate_limits 
                SET requests_count = requests_count + 1
                WHERE api_key = ? AND ip_address = ?
            ''', (api_key, ip_address))
        else:
            # First request in this window
            cursor.execute('''
                INSERT OR REPLACE INTO rate_limits (api_key, ip_address, requests_count)
                VALUES (?, ?, 1)
            ''', (api_key, ip_address))
        
        conn.commit()
        conn.close()
        return True
    
    def is_blocked(self, ip_address, user_agent):
        """Check if IP or User Agent is blocked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT reason FROM blocked_access 
            WHERE ip_address = ? OR user_agent = ?
        ''', (ip_address, user_agent))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None, result[0] if result else None
    
    def auto_block_scraper(self, ip_address, user_agent, reason):
        """Automatically block suspicious scraping activity - NEVER BLOCK BROWSERS"""
        # Check if this is a browser user agent
        browser_indicators = [
            'mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera',
            'webkit', 'gecko', 'trident', 'blink', 'presto', 'electron',
            'vscode', 'msie', 'seamonkey', 'konqueror', 'lynx'
        ]
        
        user_agent_lower = user_agent.lower()
        is_browser = any(indicator in user_agent_lower for indicator in browser_indicators)
        
        # NEVER auto-block browsers
        if is_browser:
            return
        
        # Only block non-browser automation tools
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO blocked_access (ip_address, user_agent, reason, auto_block)
            VALUES (?, ?, ?, TRUE)
        ''', (ip_address, user_agent, reason))
        
        conn.commit()
        conn.close()
    
    def clear_browser_blocks(self):
        """Clear any existing blocks for browser user agents"""
        browser_indicators = [
            'mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera',
            'webkit', 'gecko', 'trident', 'blink', 'presto', 'electron',
            'vscode', 'msie', 'seamonkey', 'konqueror', 'lynx'
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove any blocks for browser user agents
        for indicator in browser_indicators:
            cursor.execute('''
                DELETE FROM blocked_access 
                WHERE LOWER(user_agent) LIKE ?
            ''', (f'%{indicator}%',))
        
        # Also clear localhost blocks (development environment)
        cursor.execute('''
            DELETE FROM blocked_access 
            WHERE ip_address IN ('127.0.0.1', '::1', 'localhost')
        ''')
        
        conn.commit()
        conn.close()

# Anti-scraping middleware
def detect_scraping_behavior(request):
    """Detect potential scraping behavior - BROWSERS ARE COMPLETELY EXEMPT"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # FIRST: Check if this is ANY kind of browser - if so, NEVER block
    browser_indicators = [
        'mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera',
        'webkit', 'gecko', 'trident', 'blink', 'presto', 'electron',
        'vscode', 'msie', 'seamonkey', 'konqueror', 'lynx'
    ]
    
    # If ANY browser indicator is present, immediately allow
    is_browser = any(indicator in user_agent for indicator in browser_indicators)
    if is_browser:
        return False, None
    
    # If no user agent at all, allow it (could be a browser with privacy settings)
    if not user_agent:
        return False, None
    
    # Only block VERY OBVIOUS automation tools that clearly identify themselves
    obvious_automation_tools = [
        'scrapy', 'python-requests', 'urllib/', 'curl/', 'wget/', 
        'httpie/', 'postman', 'insomnia', 'rest-client', 'api-client',
        'selenium', 'phantomjs', 'headless', 'mechanize', 'requests/',
        'python-urllib', 'libwww-perl', 'java/', 'go-http-client'
    ]
    
    # Only block if it's a VERY OBVIOUS automation tool
    for tool in obvious_automation_tools:
        if tool in user_agent and not any(browser in user_agent for browser in browser_indicators):
            return True, f"Automation tool detected: {tool}"
    
    # Default: Allow access (be extremely permissive)
    return False, None

# Global API key manager instance
api_manager = APIKeyManager()
