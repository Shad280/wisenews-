# WiseNews Auto-Refresh Configuration
import schedule
import time
import threading
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NewsScheduler:
    def __init__(self, app):
        self.app = app
        self.is_running = False
        
    def start_scheduler(self):
        """Start the background news scheduler"""
        if not self.is_running:
            self.is_running = True
            scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            scheduler_thread.start()
            logging.info("WiseNews scheduler started")
    
    def _run_scheduler(self):
        """Background thread that runs the scheduler"""
        # Schedule different types of news at different intervals
        
        # Breaking news and general updates - every 30 minutes
        schedule.every(30).minutes.do(self._fetch_general_news)
        
        # Business and finance - every 15 minutes (market hours)
        schedule.every(15).minutes.do(self._fetch_business_news)
        
        # Technology news - every 2 hours
        schedule.every(2).hours.do(self._fetch_tech_news)
        
        # Full refresh - every 6 hours
        schedule.every(6).hours.do(self._full_refresh)
        
        # Daily cleanup - once per day at 3 AM
        schedule.every().day.at("03:00").do(self._daily_cleanup)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _fetch_general_news(self):
        """Fetch general news updates"""
        try:
            from news_aggregator import aggregate_news
            logging.info("Starting scheduled general news fetch")
            aggregate_news()
            logging.info("General news fetch completed")
        except Exception as e:
            logging.error(f"Error in general news fetch: {e}")
    
    def _fetch_business_news(self):
        """Fetch business news (during market hours only)"""
        try:
            current_hour = datetime.now().hour
            # Only during market hours (9 AM - 4 PM EST, adjust for your timezone)
            if 9 <= current_hour <= 16:
                from news_aggregator import aggregate_news
                logging.info("Starting scheduled business news fetch")
                # You could modify this to fetch only business sources
                aggregate_news()
                logging.info("Business news fetch completed")
        except Exception as e:
            logging.error(f"Error in business news fetch: {e}")
    
    def _fetch_tech_news(self):
        """Fetch technology news"""
        try:
            from news_aggregator import aggregate_news
            logging.info("Starting scheduled tech news fetch")
            aggregate_news()
            logging.info("Tech news fetch completed")
        except Exception as e:
            logging.error(f"Error in tech news fetch: {e}")
    
    def _full_refresh(self):
        """Full news refresh"""
        try:
            from news_aggregator import aggregate_news
            logging.info("Starting full news refresh")
            aggregate_news()
            logging.info("Full news refresh completed")
        except Exception as e:
            logging.error(f"Error in full refresh: {e}")
    
    def _daily_cleanup(self):
        """Daily maintenance tasks"""
        try:
            logging.info("Starting daily cleanup")
            # Add cleanup tasks here (delete old articles, etc.)
            logging.info("Daily cleanup completed")
        except Exception as e:
            logging.error(f"Error in daily cleanup: {e}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logging.info("WiseNews scheduler stopped")

# Configuration settings you can adjust
NEWS_CONFIG = {
    'GENERAL_NEWS_INTERVAL': 30,  # minutes
    'BUSINESS_NEWS_INTERVAL': 15,  # minutes  
    'TECH_NEWS_INTERVAL': 120,    # minutes (2 hours)
    'FULL_REFRESH_INTERVAL': 360,  # minutes (6 hours)
    'ENABLE_AUTO_REFRESH': True,
    'QUIET_HOURS_START': 23,      # 11 PM
    'QUIET_HOURS_END': 6,         # 6 AM
    'MARKET_HOURS_START': 9,      # 9 AM
    'MARKET_HOURS_END': 16        # 4 PM
}
