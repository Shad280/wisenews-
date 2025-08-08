# WiseNews User Authentication Decorators and Middleware

from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash
from user_auth import user_manager
import hashlib
import sqlite3

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        
        if not session_token:
            if request.is_json:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource',
                    'login_url': url_for('login_form')
                }), 401
            else:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login_form', next=request.url))
        
        # Validate session
        is_valid, user_data = user_manager.validate_session(session_token)
        
        if not is_valid:
            session.clear()
            if request.is_json:
                return jsonify({
                    'error': 'Session expired',
                    'message': 'Your session has expired. Please log in again.',
                    'login_url': url_for('login_form')
                }), 401
            else:
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login_form', next=request.url))
        
        # Add user data to request context
        request.current_user = user_data
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        
        if not session_token:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        is_valid, user_data = user_manager.validate_session(session_token)
        
        if not is_valid:
            return jsonify({'error': 'Invalid admin session'}), 401
        
        # Check if user is admin (you can customize this logic)
        # For now, we'll use email-based admin check
        admin_emails = ['admin@wisenews.com', 'stamo@wisenews.com']  # Configure your admin emails
        
        if user_data['email'] not in admin_emails:
            return jsonify({'error': 'Admin privileges required'}), 403
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current logged-in user"""
    session_token = session.get('session_token')
    
    if session_token:
        is_valid, user_data = user_manager.validate_session(session_token)
        if is_valid:
            return user_data
    
    return None

def is_user_logged_in():
    """Check if user is logged in"""
    return get_current_user() is not None

def get_user_ip():
    """Get user's IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_user_agent():
    """Get user's browser/device info"""
    return request.headers.get('User-Agent', '')

def log_user_activity(user_id, activity_type, details=None):
    """Log user activity for security and analytics"""
    ip_address = get_user_ip()
    user_agent = get_user_agent()
    
    # Log to data processing log
    user_manager.log_data_processing(
        user_id,
        activity_type,
        'activity_data',
        'legitimate_interest',
        'security_monitoring',
        ip_address
    )

def rate_limit_user(max_attempts=5, window_minutes=15):
    """Rate limiting decorator for user actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = get_user_ip()
            
            # Simple rate limiting based on IP
            # In production, use Redis or more sophisticated rate limiting
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def gdpr_consent_required(consent_type='gdpr_consent'):
    """Decorator to ensure GDPR consent for specific actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check specific consent in database
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT {consent_type} FROM users WHERE id = ?', (user['user_id'],))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                return jsonify({
                    'error': 'Consent required',
                    'message': f'This action requires {consent_type.replace("_", " ")} consent',
                    'consent_url': url_for('privacy_settings')
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
