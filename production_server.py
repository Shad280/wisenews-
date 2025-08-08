#!/usr/bin/env python3
"""
WiseNews Production Server Startup Script
Optimized for high performance on current hardware
"""

import os
import sys
import logging
import multiprocessing
from gunicorn.app.wsgiapp import WSGIApplication

# Set production environment
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONOPTIMIZE'] = '2'  # Enable Python optimizations

class ProductionServer(WSGIApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

def get_optimal_workers():
    """Calculate optimal number of workers based on CPU cores"""
    cpu_count = multiprocessing.cpu_count()
    # For I/O intensive apps like news aggregator: 2 * CPU cores
    return min(4, cpu_count * 2)

def start_production_server():
    """Start optimized production server"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        handlers=[
            logging.FileHandler('logs/production.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting WiseNews Production Server...")
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('cache', exist_ok=True)
    
    # Import the Flask app
    from app import app
    
    # Production server configuration
    options = {
        'bind': '0.0.0.0:5000',
        'workers': get_optimal_workers(),
        'worker_class': 'gthread',
        'threads': 2,
        'worker_connections': 1000,
        'max_requests': 1000,
        'max_requests_jitter': 50,
        'preload_app': True,
        'timeout': 30,
        'keepalive': 5,
        'graceful_timeout': 30,
        'user': None,  # Run as current user
        'group': None,
        'tmp_upload_dir': None,
        'secure_scheme_headers': {
            'X-FORWARDED-PROTOCOL': 'ssl',
            'X-FORWARDED-PROTO': 'https',
            'X-FORWARDED-SSL': 'on'
        },
        'forwarded_allow_ips': '*',
        'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
        'accesslog': 'logs/access.log',
        'errorlog': 'logs/error.log',
        'loglevel': 'info',
        'capture_output': True,
        'enable_stdio_inheritance': True
    }
    
    logger.info(f"Configuration: {get_optimal_workers()} workers, gthread class")
    logger.info("Server optimized for:")
    logger.info("- High concurrent user load")
    logger.info("- Memory efficient operation")
    logger.info("- Anti-scraping protection")
    logger.info("- Database connection pooling")
    logger.info("- Response caching")
    
    # Start the server
    ProductionServer(app, options).run()

if __name__ == '__main__':
    start_production_server()
