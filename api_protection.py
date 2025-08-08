# WiseNews API Protection Middleware

from functools import wraps
from flask import request, jsonify, abort, render_template
from api_security import api_manager, detect_scraping_behavior
import time

def require_api_key(f):
    """Decorator to require valid API key for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key parameter',
                'apply_url': request.url_root + 'api/apply'
            }), 401
        
        # Validate API key
        is_valid, rate_limit, usage_count = api_manager.validate_api_key(api_key)
        
        if not is_valid:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'API key is invalid, expired, or pending approval',
                'apply_url': request.url_root + 'api/apply'
            }), 403
        
        # Check rate limits
        ip_address = request.remote_addr
        if not api_manager.check_rate_limit(api_key, ip_address, rate_limit):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'You have exceeded the rate limit of {rate_limit} requests per hour',
                'reset_time': time.time() + 3600  # Reset in 1 hour
            }), 429
        
        # Log API usage
        api_manager.log_api_usage(
            api_key, 
            request.endpoint, 
            ip_address,
            request.headers.get('User-Agent', ''),
            200
        )
        
        return f(*args, **kwargs)
    
    return decorated_function

def anti_scraping_protection(f):
    """Decorator to protect against scraping - BROWSERS ARE NEVER BLOCKED"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # BROWSER PROTECTION: Always allow legitimate browsers
        browser_patterns = [
            'mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera', 
            'webkit', 'gecko', 'trident', 'blink', 'presto'
        ]
        
        # If it's a browser, ALWAYS allow access without any checks
        is_browser = any(pattern in user_agent for pattern in browser_patterns)
        if is_browser:
            return f(*args, **kwargs)
        
        # Only apply security checks to non-browser requests
        # Check if IP/User Agent is blocked
        is_blocked, block_reason = api_manager.is_blocked(ip_address, user_agent)
        
        if is_blocked:
            return jsonify({
                'error': '🌟 WiseNews Service Temporarily Unavailable',
                'message': 'Our premium news service is experiencing high demand! Please visit our website directly for the latest breaking news and insights.',
                'website': request.url_root.rstrip('/'),
                'brand': 'WiseNews - Your Trusted Source for Intelligent News'
            }), 503
        
        # Detect scraping behavior (only for non-browsers)
        is_scraping, scraping_reason = detect_scraping_behavior(request)
        
        if is_scraping:
            # Auto-block suspicious activity
            api_manager.auto_block_scraper(ip_address, user_agent, scraping_reason)
            
            # User-friendly error message without technical details
            return jsonify({
                'error': '🌟 WiseNews Premium Access Required',
                'message': 'This advanced feature requires WiseNews API access. Visit our website to explore our comprehensive news coverage and apply for API access!',
                'website': request.url_root.rstrip('/'),
                'api_info': request.url_root.rstrip('/') + '/api/docs',
                'brand': 'WiseNews - Intelligent News, Delivered Smart'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def browser_only(f):
    """Decorator to allow browser access - VERY LENIENT"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # Allow requests with any browser-like user agent or VS Code browser
        browser_patterns = [
            'mozilla', 'chrome', 'firefox', 'safari', 'edge', 'opera',
            'webkit', 'gecko', 'trident', 'blink', 'presto', 'vscode'
        ]
        
        # Very lenient - if there's ANY browser indicator OR no obvious bot pattern, allow it
        has_browser_pattern = any(pattern in user_agent for pattern in browser_patterns)
        
        # Block only obvious non-browser automation tools
        obvious_bots = ['curl', 'wget', 'scrapy', 'python-requests', 'urllib']
        is_obvious_bot = any(bot in user_agent for bot in obvious_bots)
        
        if not has_browser_pattern and is_obvious_bot:
            return render_template('api_access_denied.html'), 403
        
        # Default: allow access (be very permissive for browsers)
        return f(*args, **kwargs)
    
    return decorated_function
