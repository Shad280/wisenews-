"""
Subscription Management Module for WiseNews
Handles subscription tiers, trials, and usage tracking
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from functools import wraps

class SubscriptionManager:
    def __init__(self, db_path='news_database.db'):
        self.db_path = db_path
    
    def _parse_json_safely(self, json_str):
        """Safely parse JSON string, return empty list on error"""
        if not json_str or not json_str.strip():
            return []
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return []
    
    def get_user_subscription(self, user_id):
        """Get current active subscription for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT us.*, sp.name, sp.display_name, sp.features, sp.max_articles_per_day,
                   sp.max_searches_per_day, sp.max_bookmarks, sp.api_access,
                   sp.priority_support, sp.advanced_filters, sp.export_data
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.id
            WHERE us.user_id = ? AND us.status IN ('active', 'trial')
            ORDER BY us.created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'user_id': result[1],
                'plan_id': result[2],
                'status': result[3],
                'trial_start_date': result[4],
                'trial_end_date': result[5],
                'subscription_start_date': result[6],
                'subscription_end_date': result[7],
                'auto_renew': result[8],
                'plan_name': result[13],
                'plan_display_name': result[14],
                'features': self._parse_json_safely(result[15]),
                'max_articles_per_day': result[16],
                'max_searches_per_day': result[17],
                'max_bookmarks': result[18],
                'api_access': result[19],
                'priority_support': result[20],
                'advanced_filters': result[21],
                'export_data': result[22]
            }
        return None
    
    def start_free_trial(self, user_id):
        """Start a 7-day free trial for new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user already had a trial
        cursor.execute('''
            SELECT id FROM user_subscriptions 
            WHERE user_id = ? AND status = 'trial'
        ''', (user_id,))
        
        if cursor.fetchone():
            conn.close()
            return False, "User already used free trial"
        
        # Get free plan ID
        cursor.execute("SELECT id FROM subscription_plans WHERE name = 'free'")
        plan_id = cursor.fetchone()[0]
        
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=7)
        
        cursor.execute('''
            INSERT INTO user_subscriptions 
            (user_id, plan_id, status, trial_start_date, trial_end_date)
            VALUES (?, ?, 'trial', ?, ?)
        ''', (user_id, plan_id, trial_start, trial_end))
        
        conn.commit()
        conn.close()
        return True, "Free trial started successfully"
    
    def check_trial_expiry(self, user_id):
        """Check if trial has expired and update status"""
        subscription = self.get_user_subscription(user_id)
        if not subscription or subscription['status'] != 'trial':
            return False
        
        if subscription['trial_end_date']:
            trial_end = datetime.fromisoformat(subscription['trial_end_date'])
            if datetime.now() > trial_end:
                # Mark trial as expired
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_subscriptions 
                    SET status = 'expired' 
                    WHERE id = ?
                ''', (subscription['id'],))
                conn.commit()
                conn.close()
                return True
        return False
    
    def get_daily_usage(self, user_id, date=None):
        """Get user's daily usage statistics"""
        if date is None:
            date = datetime.now().date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT articles_viewed, searches_performed, bookmarks_created, api_requests
            FROM usage_tracking
            WHERE user_id = ? AND date = ?
        ''', (user_id, date))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'articles_viewed': result[0],
                'searches_performed': result[1],
                'bookmarks_created': result[2],
                'api_requests': result[3]
            }
        else:
            return {
                'articles_viewed': 0,
                'searches_performed': 0,
                'bookmarks_created': 0,
                'api_requests': 0
            }
    
    def track_usage(self, user_id, usage_type, increment=1):
        """Track user usage (articles_viewed, searches_performed, etc.)"""
        today = datetime.now().date()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update usage tracking
        cursor.execute('''
            INSERT INTO usage_tracking (user_id, date, {})
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
            {} = {} + ?
        '''.format(usage_type, usage_type, usage_type), 
        (user_id, today, increment, increment))
        
        conn.commit()
        conn.close()
    
    def check_usage_limit(self, user_id, usage_type):
        """Check if user has exceeded their daily limit"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False, "No active subscription"
        
        # Check if trial expired
        if subscription['status'] == 'trial':
            self.check_trial_expiry(user_id)
            subscription = self.get_user_subscription(user_id)
            if not subscription:
                return False, "Trial expired"
        
        usage = self.get_daily_usage(user_id)
        
        # Normalize usage_type for consistency
        usage_type_map = {
            'articles': 'articles_viewed',
            'searches': 'searches_performed', 
            'bookmarks': 'bookmarks_created',
            'api': 'api_requests'
        }
        
        # Use mapped type or original if not found
        actual_usage_type = usage_type_map.get(usage_type, usage_type)
        
        # Get limits based on usage type, with safety checks
        limit_map = {
            'articles_viewed': subscription.get('max_articles_per_day', 0) if subscription else 0,
            'searches_performed': subscription.get('max_searches_per_day', 0) if subscription else 0,
            'bookmarks_created': subscription.get('max_bookmarks', 0) if subscription else 0,
            'api_requests': 1000 if subscription and subscription.get('api_access') else 0
        }
        
        # Safe conversion handling JSON data
        limit_value = limit_map.get(actual_usage_type, 0) or 0
        if isinstance(limit_value, str):
            try:
                # Try to parse as JSON first
                parsed_value = json.loads(limit_value)
                if isinstance(parsed_value, list):
                    # Extract numeric value from list descriptions
                    for item in parsed_value:
                        if isinstance(item, str) and 'articles per day' in item.lower():
                            # Extract number from string like "Up to 10 articles per day"
                            numbers = re.findall(r'\d+', item)
                            if numbers:
                                limit = int(numbers[0])
                                break
                    else:
                        limit = 10  # Default limit
                else:
                    limit = int(parsed_value) if str(parsed_value).isdigit() else 10
            except (json.JSONDecodeError, ValueError):
                # If not JSON, try direct int conversion
                if str(limit_value).isdigit():
                    limit = int(limit_value)
                else:
                    limit = 10  # Default safe limit
        else:
            limit = int(limit_value) if limit_value else 10
        current_usage = int(usage.get(actual_usage_type, 0) or 0)
        
        # -1 means unlimited
        if limit == -1:
            return True, "Unlimited"
        
        if current_usage >= limit:
            return False, f"Daily limit of {limit} reached"
        
        return True, f"{current_usage}/{limit} used"
    
    def get_all_plans(self):
        """Get all available subscription plans"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, description, price_monthly, price_yearly,
                   features, max_articles_per_day, max_searches_per_day, max_bookmarks,
                   api_access, priority_support, advanced_filters, export_data
            FROM subscription_plans
            WHERE is_active = TRUE
            ORDER BY price_monthly ASC
        ''')
        
        plans = []
        for row in cursor.fetchall():
            plans.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'price_monthly': float(row[4]) if row[4] else 0,
                'price_yearly': float(row[5]) if row[5] else 0,
                'features': json.loads(row[6]) if row[6] else [],
                'max_articles_per_day': row[7],
                'max_searches_per_day': row[8],
                'max_bookmarks': row[9],
                'api_access': row[10],
                'priority_support': row[11],
                'advanced_filters': row[12],
                'export_data': row[13]
            })
        
        conn.close()
        return plans

def subscription_required(subscription_manager, usage_type=None):
    """Decorator to check subscription requirements"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, redirect, url_for, flash
            
            if 'user_id' not in session:
                flash('Please log in to access this feature.', 'error')
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            subscription = subscription_manager.get_user_subscription(user_id)
            
            if not subscription:
                flash('Please subscribe to access this feature.', 'error')
                return redirect(url_for('subscription_plans'))
            
            if usage_type:
                can_use, message = subscription_manager.check_usage_limit(user_id, usage_type)
                if not can_use:
                    flash(f'Usage limit exceeded: {message}', 'error')
                    return redirect(url_for('subscription_plans'))
                
                # Track the usage
                subscription_manager.track_usage(user_id, usage_type)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_access_required(subscription_manager):
    """Decorator specifically for API access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify
            
            # Get user from API key (you'll need to implement this)
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Here you would validate the API key and get user_id
            # For now, we'll assume you have a function to do this
            user_id = validate_api_key(api_key)  # You need to implement this
            if not user_id:
                return jsonify({'error': 'Invalid API key'}), 401
            
            subscription = subscription_manager.get_user_subscription(user_id)
            if not subscription or not subscription['api_access']:
                return jsonify({'error': 'API access not available in your plan'}), 403
            
            can_use, message = subscription_manager.check_usage_limit(user_id, 'api_requests')
            if not can_use:
                return jsonify({'error': f'API limit exceeded: {message}'}), 429
            
            # Track API usage
            subscription_manager.track_usage(user_id, 'api_requests')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_api_key(api_key):
    """Validate API key and return user_id"""
    # This function should validate the API key against your database
    # and return the associated user_id
    # Implementation depends on your API key storage method
    pass
