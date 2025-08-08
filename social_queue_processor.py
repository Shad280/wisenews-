"""
Social Media Content Queue Processor
Runs as a background service to process scheduled social media posts
"""

import time
import logging
from social_media_manager import social_media_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_social_queue_processor():
    """Main loop for processing social media content queue"""
    logger.info("Starting Social Media Content Queue Processor")
    
    while True:
        try:
            # Process the content queue
            social_media_manager.process_content_queue()
            
            # Monitor social trends
            social_media_manager.monitor_social_trends()
            
            # Wait 5 minutes before next processing cycle
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            logger.info("Social Media Queue Processor stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in social queue processor: {e}")
            # Wait 1 minute before retrying on error
            time.sleep(60)

if __name__ == "__main__":
    run_social_queue_processor()
