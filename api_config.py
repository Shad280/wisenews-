"""
API Configuration for WiseNews Enhanced Data Sources
Update this file with your actual API keys to enable enhanced data sources
"""

# News APIs
NEWSAPI_KEY = "your_newsapi_key_here"  # Get from https://newsapi.org/
CURRENTS_API_KEY = "your_currents_api_key"  # Get from https://currentsapi.services/
MEDIASTACK_API_KEY = "your_mediastack_key"  # Get from https://mediastack.com/

# Financial Data APIs
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key"  # Get from https://www.alphavantage.co/
POLYGON_API_KEY = "your_polygon_key"  # Get from https://polygon.io/
IEX_API_TOKEN = "your_iex_token"  # Get from https://iexcloud.io/
FINNHUB_API_KEY = "your_finnhub_key"  # Get from https://finnhub.io/
QUANDL_API_KEY = "your_quandl_key"  # Get from https://www.quandl.com/

# Cryptocurrency APIs
COINMARKETCAP_API_KEY = "your_coinmarketcap_key"  # Get from https://pro.coinmarketcap.com/
# CoinGecko is free and doesn't require API key

# Government APIs
FRED_API_KEY = "your_fred_key"  # Get from https://fred.stlouisfed.org/docs/api/

# Social Media APIs
REDDIT_CLIENT_ID = "your_reddit_client_id"
REDDIT_CLIENT_SECRET = "your_reddit_client_secret"
YOUTUBE_API_KEY = "your_youtube_api_key"
TWITTER_BEARER_TOKEN = "your_twitter_bearer_token"

# Alternative Data
GOOGLE_TRENDS_API_KEY = "your_google_trends_key"
PLANET_API_KEY = "your_planet_api_key"

# Configuration flags
ENABLE_NEWSAPI = False  # Set to True when you have the API key
ENABLE_FINANCIAL_APIS = False  # Set to True when you have financial API keys
ENABLE_CRYPTO_APIS = True  # CoinGecko works without API key
ENABLE_GOVERNMENT_APIS = True  # Many government feeds are open
ENABLE_SOCIAL_APIS = False  # Set to True when you have social media API keys

# Rate limiting settings
API_RATE_LIMITS = {
    'newsapi': 1000,  # requests per day
    'alpha_vantage': 5,  # requests per minute (free tier)
    'coingecko': 50,  # requests per minute
    'reddit': 60,  # requests per minute
    'polygon': 5,  # requests per minute (free tier)
    'iex': 500000,  # monthly core data credits
    'finnhub': 60  # requests per minute (free tier)
}

# Data source priorities (1-10, higher = more important)
SOURCE_PRIORITIES = {
    'breaking_news': 10,
    'government': 9,
    'financial': 8,
    'crypto': 7,
    'news': 6,
    'social': 5,
    'alternative': 4
}

# Update intervals (in minutes)
UPDATE_INTERVALS = {
    'breaking_news': 5,
    'financial': 15,
    'crypto': 10,
    'news': 30,
    'government': 60,
    'social': 20
}

def get_api_key(service):
    """Get API key for a service"""
    key_mapping = {
        'newsapi': NEWSAPI_KEY,
        'alpha_vantage': ALPHA_VANTAGE_API_KEY,
        'coinmarketcap': COINMARKETCAP_API_KEY,
        'polygon': POLYGON_API_KEY,
        'iex': IEX_API_TOKEN,
        'finnhub': FINNHUB_API_KEY,
        'fred': FRED_API_KEY,
        'reddit_id': REDDIT_CLIENT_ID,
        'reddit_secret': REDDIT_CLIENT_SECRET,
        'youtube': YOUTUBE_API_KEY,
        'twitter': TWITTER_BEARER_TOKEN
    }
    
    return key_mapping.get(service, '')

def is_service_enabled(service):
    """Check if a service is enabled"""
    service_flags = {
        'newsapi': ENABLE_NEWSAPI,
        'financial': ENABLE_FINANCIAL_APIS,
        'crypto': ENABLE_CRYPTO_APIS,
        'government': ENABLE_GOVERNMENT_APIS,
        'social': ENABLE_SOCIAL_APIS
    }
    
    return service_flags.get(service, False)
