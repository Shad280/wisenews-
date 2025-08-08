#!/usr/bin/env python3
"""
Fix Unicode logging issues in live events manager
"""

import re
import os

def fix_unicode_logging():
    """Fix Unicode logging issues in live_events_manager.py"""
    try:
        with open('live_events_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add import for handling Unicode properly
        import_section = '''import sqlite3
import json
import requests
import time
import threading
import random
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, List, Optional, Tuple
from database_manager import db_manager

# Configure logging to handle Unicode properly on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Handle Windows encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)'''
        
        # Replace the import section
        pattern = r'import sqlite3.*?logger = logging\.getLogger\(__name__\)'
        content = re.sub(pattern, import_section, content, flags=re.DOTALL)
        
        # Replace emoji characters in log messages with text equivalents
        emoji_replacements = {
            '📈': '[UP]',
            '📉': '[DOWN]', 
            '🔄': '[REFRESH]',
            '⚽': '[FOOTBALL]',
            '🏀': '[BASKETBALL]',
            '🎾': '[TENNIS]',
            '⚾': '[BASEBALL]',
            '🎯': '[TARGET]',
            '🟨': '[YELLOW]',
            '🟥': '[RED]',
            '🏦': '[BANK]',
            '⚖️': '[LEGAL]',
            '📊': '[CHART]',
            '📋': '[DOCUMENT]',
            '💰': '[MONEY]',
            '📢': '[ANNOUNCEMENT]'
        }
        
        for emoji, text in emoji_replacements.items():
            content = content.replace(emoji, text)
        
        # Write the fixed content back
        with open('live_events_manager.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed Unicode logging issues in live_events_manager.py")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Unicode logging: {e}")
        return False

if __name__ == "__main__":
    fix_unicode_logging()
