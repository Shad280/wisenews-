# Production Configuration for WiseNews
import os
import multiprocessing

# Flask Application Settings
DEBUG = False
TESTING = False
ENV = 'production'

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'wisenews-secure-production-key-2025-v2')
WTF_CSRF_ENABLED = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Database Optimization
DATABASE_POOL_SIZE = 20
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
DATABASE_ECHO = False

# Caching Configuration
CACHE_TYPE = 'filesystem'
CACHE_DIR = 'cache'
CACHE_DEFAULT_TIMEOUT = 300
CACHE_THRESHOLD = 1000

# Performance Settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
JSON_SORT_KEYS = False
JSONIFY_PRETTYPRINT_REGULAR = False

# Threading and Process Settings
WORKERS = min(4, multiprocessing.cpu_count())
THREADS = 2
WORKER_CONNECTIONS = 1000
MAX_REQUESTS = 1000
MAX_REQUESTS_JITTER = 50

# Gunicorn Settings
bind = "127.0.0.1:5000"
worker_class = "gthread"
worker_tmp_dir = "/dev/shm"  # Use RAM for temp files
preload_app = True
keepalive = 5
timeout = 30
graceful_timeout = 30

# Rate Limiting
RATELIMIT_STORAGE_URL = "memory://"
RATELIMIT_DEFAULT = "100 per hour"

# Logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/wisenews.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

# Memory Management
MEMORY_LIMIT = 512  # MB per worker
MEMORY_CHECK_INTERVAL = 30  # seconds

# Database Connection Pool Settings
DATABASE_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}

# Static File Optimization
SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
STATIC_FOLDER_OPTIMIZATION = True

# Compression Settings
COMPRESS_MIMETYPES = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
    'application/xml+rss',
    'application/atom+xml',
    'image/svg+xml'
]

# API Rate Limits (Very Restrictive for Anti-Scraping)
API_RATE_LIMITS = {
    'global': '1000 per hour',
    'per_ip': '100 per hour',  # Very restrictive
    'articles_per_ip': '20 per hour',  # Super restrictive
    'searches_per_ip': '10 per hour',
    'api_requests_per_ip': '50 per hour'
}

# Background Task Settings
SCHEDULER_EXECUTORS = {
    'default': {'type': 'threadpool', 'max_workers': 3}
}

# RSS Processing Optimization
RSS_BATCH_SIZE = 50
RSS_CONCURRENT_REQUESTS = 10
RSS_TIMEOUT = 15
RSS_RETRY_ATTEMPTS = 3

# Image Processing Optimization
IMAGE_PROCESSING_QUEUE_SIZE = 100
IMAGE_PROCESSING_WORKERS = 2
IMAGE_CACHE_SIZE = 500  # MB
IMAGE_QUALITY = 85
IMAGE_MAX_SIZE = (1200, 800)

# Memory Usage Monitoring
MEMORY_THRESHOLDS = {
    'warning': 70,  # 70% memory usage warning
    'critical': 85,  # 85% memory usage critical
    'restart': 90   # 90% memory usage triggers restart
}
