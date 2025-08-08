# WiseNews Security Configuration

# API Security Settings
API_SECURITY = {
    'ADMIN_KEY': 'wisenews_admin_2025',  # Change this in production!
    'DEFAULT_RATE_LIMIT': 100,
    'MAX_RATE_LIMIT': 10000,
    'RATE_LIMIT_WINDOW': 3600,  # 1 hour in seconds
    'AUTO_BLOCK_THRESHOLD': 5,  # Auto-block after 5 suspicious requests
}

# Anti-Scraping Configuration
ANTI_SCRAPING = {
    'ENABLED': True,
    'BLOCK_BOTS': True,
    'CHECK_USER_AGENT': True,
    'CHECK_HEADERS': True,
    'BROWSER_REQUIRED_ROUTES': ['/', '/articles', '/search'],
    'API_ONLY_ROUTES': ['/api/articles', '/api/sync', '/api/duplicate-stats'],
}

# Blocked User Agents (will be auto-blocked)
BLOCKED_USER_AGENTS = [
    'scrapy',
    'requests',
    'urllib',
    'curl',
    'wget',
    'python-requests',
    'bot',
    'crawler',
    'spider',
    'scraper',
    'automation',
    'selenium',
    'phantomjs',
    'headless',
    'mechanize',
    'okhttp',
    'apache-httpclient',
]

# Allowed browsers
ALLOWED_BROWSERS = [
    'chrome',
    'firefox',
    'safari',
    'edge',
    'opera',
    'mobile',
    'tablet',
]

# Security Headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com; script-src 'self' 'unsafe-inline' https://code.jquery.com https://stackpath.bootstrapcdn.com;",
}

# Rate Limiting Tiers
RATE_LIMIT_TIERS = {
    'free': {
        'requests_per_hour': 100,
        'description': 'Free tier for personal use'
    },
    'premium': {
        'requests_per_hour': 1000,
        'description': 'Premium tier for small businesses'
    },
    'enterprise': {
        'requests_per_hour': 10000,
        'description': 'Enterprise tier for large organizations'
    }
}

# Auto-block triggers
AUTO_BLOCK_TRIGGERS = {
    'rapid_requests': 10,  # Block if >10 requests in 1 minute
    'missing_headers': True,  # Block if missing browser headers
    'suspicious_user_agent': True,  # Block known scrapers
    'invalid_api_attempts': 5,  # Block after 5 invalid API key attempts
}
