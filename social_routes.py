"""
Social Media Authentication Routes for WiseNews
Handles OAuth flows, social login, and account management
"""

from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template, flash
from social_media_manager import social_media_manager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create blueprint for social media routes
social_bp = Blueprint('social', __name__, url_prefix='/social')

@social_bp.route('/connect/<platform>')
def connect_social_account(platform):
    """Initiate social media account connection"""
    
    if 'user_id' not in session:
        flash('Please log in to connect social media accounts', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    redirect_uri = url_for('social.oauth_callback', platform=platform, _external=True)
    
    # Generate OAuth URL
    oauth_url = social_media_manager.create_oauth_url(platform, user_id, redirect_uri)
    
    if not oauth_url:
        flash(f'Social media platform {platform} is not supported', 'error')
        return redirect(url_for('dashboard'))
    
    return redirect(oauth_url)

@social_bp.route('/callback/<platform>')
def oauth_callback(platform):
    """Handle OAuth callback from social media platforms"""
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        flash(f'Social media connection failed: {error}', 'error')
        return redirect(url_for('dashboard'))
    
    if not code or not state:
        flash('Invalid social media callback', 'error')
        return redirect(url_for('dashboard'))
    
    # Handle OAuth callback
    success = social_media_manager.handle_oauth_callback(platform, code, state)
    
    if success:
        flash(f'Successfully connected your {platform.title()} account!', 'success')
    else:
        flash(f'Failed to connect {platform.title()} account', 'error')
    
    return redirect(url_for('dashboard'))

@social_bp.route('/share/<int:article_id>')
def share_article(article_id):
    """Share specific article to social media"""
    
    platforms = request.args.getlist('platforms')
    if not platforms:
        platforms = ['twitter', 'linkedin']  # Default platforms
    
    try:
        # Get article data
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, content, category, url, image_url
            FROM news WHERE id = ?
        ''', (article_id,))
        
        article = cursor.fetchone()
        conn.close()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        article_data = {
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'category': article[3],
            'url': article[4] or f"{request.host_url}article/{article_id}",
            'image_url': article[5]
        }
        
        # Post to social media
        success = social_media_manager.auto_post_breaking_news(article_data, platforms)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Article shared to {", ".join(platforms)}',
                'platforms': platforms
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to share article'
            }), 500
            
    except Exception as e:
        logger.error(f"Error sharing article: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@social_bp.route('/queue', methods=['POST'])
def queue_for_posting():
    """Queue content for scheduled social media posting"""
    
    data = request.get_json()
    
    required_fields = ['content_type', 'reference_id', 'platforms']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        from datetime import datetime
        
        scheduled_time = None
        if data.get('scheduled_time'):
            scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        
        success = social_media_manager.queue_content_for_posting(
            content_data=data.get('content_data', {}),
            platforms=data['platforms'],
            priority=data.get('priority', 1),
            scheduled_time=scheduled_time
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Content queued for posting'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to queue content'
            }), 500
            
    except Exception as e:
        logger.error(f"Error queuing content: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@social_bp.route('/analytics')
def social_analytics():
    """Get social media analytics dashboard"""
    
    days = request.args.get('days', 30, type=int)
    
    try:
        analytics_data = social_media_manager.get_social_analytics(days)
        trends_data = social_media_manager.monitor_social_trends()
        
        return render_template('social_analytics.html', 
                             analytics=analytics_data, 
                             trends=trends_data,
                             days=days,
                             current_time=datetime.now())
                             
    except Exception as e:
        logger.error(f"Error getting social analytics: {e}")
        flash('Error loading social media analytics', 'error')
        return redirect(url_for('dashboard'))

@social_bp.route('/api/analytics')
def api_social_analytics():
    """API endpoint for social media analytics"""
    
    days = request.args.get('days', 30, type=int)
    
    try:
        analytics_data = social_media_manager.get_social_analytics(days)
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error getting social analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@social_bp.route('/api/trends')
def api_social_trends():
    """API endpoint for social media trends"""
    
    try:
        trends_data = social_media_manager.monitor_social_trends()
        return jsonify({'trends': trends_data})
        
    except Exception as e:
        logger.error(f"Error getting social trends: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@social_bp.route('/settings')
def social_settings():
    """Social media settings page"""
    
    if 'user_id' not in session:
        flash('Please log in to access social media settings', 'warning')
        return redirect(url_for('login'))
    
    try:
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Get user's connected social accounts
        cursor.execute('''
            SELECT platform, username, is_active, created_at
            FROM user_social_accounts 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        connected_accounts = []
        for row in cursor.fetchall():
            connected_accounts.append({
                'platform': row[0],
                'username': row[1],
                'is_active': row[2],
                'connected_date': row[3]
            })
        
        conn.close()
        
        return render_template('social_settings.html', 
                             connected_accounts=connected_accounts)
                             
    except Exception as e:
        logger.error(f"Error loading social settings: {e}")
        flash('Error loading social media settings', 'error')
        return redirect(url_for('dashboard'))

@social_bp.route('/disconnect/<platform>', methods=['POST'])
def disconnect_social_account(platform):
    """Disconnect a social media account"""
    
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_social_accounts 
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND platform = ?
        ''', (session['user_id'], platform))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{platform.title()} account disconnected'
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting social account: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Social Login Routes (OAuth-based login)
@social_bp.route('/login/<platform>')
def social_login(platform):
    """Social media login (OAuth)"""
    
    redirect_uri = url_for('social.social_login_callback', platform=platform, _external=True)
    
    # For social login, we use a temporary user_id of 0
    oauth_url = social_media_manager.create_oauth_url(platform, 0, redirect_uri)
    
    if not oauth_url:
        flash(f'Social login with {platform} is not available', 'error')
        return redirect(url_for('login'))
    
    return redirect(oauth_url)

@social_bp.route('/login/callback/<platform>')
def social_login_callback(platform):
    """Handle social login callback"""
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        flash(f'Social login failed: {error}', 'error')
        return redirect(url_for('login'))
    
    if not code or not state:
        flash('Invalid social login callback', 'error')
        return redirect(url_for('login'))
    
    try:
        # Handle social login (mock implementation)
        # In production, you would:
        # 1. Exchange code for access token
        # 2. Get user profile from social platform
        # 3. Create or link user account
        # 4. Set session
        
        # Mock user data
        social_user_data = {
            'platform': platform,
            'social_id': f'{platform}_user_123',
            'name': f'User from {platform.title()}',
            'email': f'user@{platform}.example.com',
            'profile_image': None
        }
        
        # Check if user exists or create new user
        import sqlite3
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        # Try to find existing user with this social account
        cursor.execute('''
            SELECT u.id, u.full_name, u.email 
            FROM users u
            JOIN user_social_accounts usa ON u.id = usa.user_id
            WHERE usa.platform = ? AND usa.social_user_id = ?
        ''', (platform, social_user_data['social_id']))
        
        existing_user = cursor.fetchone()
        
        if existing_user:
            # User exists, log them in
            user_id, full_name, email = existing_user
            session['user_id'] = user_id
            session['full_name'] = full_name
            session['email'] = email
            
        else:
            # Create new user account
            cursor.execute('''
                INSERT INTO users (full_name, email, password_hash, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                social_user_data['name'],
                social_user_data['email'],
                'social_login'  # Placeholder for social login users
            ))
            
            user_id = cursor.lastrowid
            
            # Link social account
            cursor.execute('''
                INSERT INTO user_social_accounts 
                (user_id, platform, social_user_id, username, is_active)
                VALUES (?, ?, ?, ?, TRUE)
            ''', (
                user_id,
                platform,
                social_user_data['social_id'],
                social_user_data['name']
            ))
            
            # Set session
            session['user_id'] = user_id
            session['full_name'] = social_user_data['name']
            session['email'] = social_user_data['email']
        
        conn.commit()
        conn.close()
        
        flash(f'Successfully logged in with {platform.title()}!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error in social login callback: {e}")
        flash('Social login failed. Please try again.', 'error')
        return redirect(url_for('login'))

# API endpoint for sharing with AJAX
@social_bp.route('/api/share', methods=['POST'])
def api_share_content():
    """API endpoint for sharing content via AJAX"""
    
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    
    platforms = data.get('platforms', ['twitter', 'linkedin'])
    content_data = data['content']
    
    try:
        success = social_media_manager.auto_post_breaking_news(content_data, platforms)
        
        return jsonify({
            'success': success,
            'message': 'Content shared successfully' if success else 'Failed to share content',
            'platforms': platforms
        })
        
    except Exception as e:
        logger.error(f"Error in API share: {e}")
        return jsonify({'error': 'Internal server error'}), 500
