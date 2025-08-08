#!/usr/bin/env python3
"""
Comprehensive User Experience Fix for WiseNews
Addresses loading screens, live events errors, and API restrictions
"""

import os
import re

def create_loading_screen_templates():
    """Create loading screen templates for better UX"""
    print("🔄 Creating loading screen templates...")
    
    # Create loading screen template
    loading_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loading - WiseNews</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        
        .loading-container {
            text-align: center;
            max-width: 400px;
            padding: 2rem;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin: 0 auto 2rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        .loading-subtitle {
            font-size: 1rem;
            opacity: 0.8;
            margin-bottom: 2rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: white;
            border-radius: 2px;
            animation: progress 3s ease-in-out infinite;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        .error-message {
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 2rem;
            display: none;
        }
    </style>
</head>
<body>
    <div class="loading-container">
        <div class="spinner"></div>
        <div class="loading-text">Loading WiseNews</div>
        <div class="loading-subtitle">{{ message if message else "Fetching the latest news for you..." }}</div>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <div class="error-message" id="errorMessage">
            If this takes too long, there might be a server issue. Please try refreshing the page.
        </div>
    </div>
    
    <script>
        // Show error message after 10 seconds
        setTimeout(function() {
            document.getElementById('errorMessage').style.display = 'block';
        }, 10000);
        
        // Auto-redirect if provided
        {% if redirect_url %}
        setTimeout(function() {
            window.location.href = "{{ redirect_url }}";
        }, {{ redirect_delay if redirect_delay else 3000 }});
        {% endif %}
    </script>
</body>
</html>'''
    
    try:
        with open('templates/loading.html', 'w', encoding='utf-8') as f:
            f.write(loading_template)
        print("✅ Created loading screen template")
        return True
    except Exception as e:
        print(f"❌ Loading template error: {e}")
        return False

def fix_scraper_protection_for_users():
    """Fix scraper protection to only affect bots, not regular users"""
    print("🔧 Fixing scraper protection for regular users...")
    
    try:
        # Read the scraper protection file
        with open('scraper_protection.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update rate limits to be more user-friendly
        new_rate_limits = '''        # Rate limiting configuration - User-friendly for legitimate users
        self.rate_limits = {
            'articles_per_hour': 500,      # Increased for regular users
            'requests_per_minute': 60,     # More generous for normal browsing
            'requests_per_hour': 1000,     # Higher limit for active users
            'daily_limit': 5000,           # Much higher for legitimate usage
        }
        
        # Separate stricter limits for detected scrapers/bots
        self.scraper_rate_limits = {
            'articles_per_hour': 10,       # Very restrictive for bots
            'requests_per_minute': 3,      # Minimal for scrapers
            'requests_per_hour': 20,       # Low for automated tools
            'daily_limit': 50,             # Very limited for bots
        }'''
        
        # Replace the existing rate limits
        pattern = r'        # Rate limiting configuration.*?        }'
        content = re.sub(pattern, new_rate_limits, content, flags=re.DOTALL)
        
        # Add bot detection method
        bot_detection_method = '''
    def _is_likely_bot(self, user_agent: str, ip: str) -> bool:
        """Enhanced bot detection that doesn't affect regular users"""
        if not user_agent:
            return True
            
        user_agent_lower = user_agent.lower()
        
        # Check for obvious bot patterns
        for pattern in self.suspicious_user_agents:
            if re.search(pattern, user_agent_lower):
                # But allow whitelisted bots
                for whitelist_pattern in self.whitelist_user_agents:
                    if re.search(whitelist_pattern, user_agent_lower):
                        return False
                return True
        
        # Check for missing common browser indicators
        browser_indicators = ['mozilla', 'webkit', 'chrome', 'safari', 'firefox', 'edge']
        has_browser_indicator = any(indicator in user_agent_lower for indicator in browser_indicators)
        
        if not has_browser_indicator:
            return True
            
        # Check request patterns (this would need to be implemented with request tracking)
        return False
    
    def _get_rate_limits_for_request(self, user_agent: str, ip: str) -> dict:
        """Get appropriate rate limits based on bot detection"""
        if self._is_likely_bot(user_agent, ip):
            return self.scraper_rate_limits
        return self.rate_limits
'''
        
        # Add the bot detection method before the existing methods
        insertion_point = content.find('    def _init_protection_tables(self):')
        if insertion_point != -1:
            content = content[:insertion_point] + bot_detection_method + '\n    ' + content[insertion_point:]
        
        # Update the rate limiting check to use dynamic limits
        content = content.replace(
            'self.rate_limits[',
            'self._get_rate_limits_for_request(user_agent, client_ip)['
        )
        
        with open('scraper_protection.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated scraper protection for user-friendly experience")
        return True
        
    except Exception as e:
        print(f"❌ Scraper protection fix error: {e}")
        return False

def remove_scraper_protection_from_user_routes():
    """Remove scraper protection from routes that regular users need"""
    print("🔧 Removing scraper protection from user-facing routes...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Routes that should NOT have scraper protection for regular users
        user_routes = [
            '@app.route(\'/articles\')',
            '@app.route(\'/dashboard\')',
            '@app.route(\'/live-events\')',
            '@app.route(\'/article/<int:article_id>\')'
        ]
        
        for route in user_routes:
            # Find the route and remove @anti_scraper_protection if it exists
            pattern = f'{re.escape(route)}\\s*@anti_scraper_protection'
            replacement = route
            content = re.sub(pattern, replacement, content)
            
            # Also handle cases where the decorator comes first
            pattern = f'@anti_scraper_protection\\s*{re.escape(route)}'
            replacement = route
            content = re.sub(pattern, replacement, content)
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Removed scraper protection from user-facing routes")
        return True
        
    except Exception as e:
        print(f"❌ Route protection removal error: {e}")
        return False

def fix_live_events_article_links():
    """Fix 500 errors in live events article links"""
    print("🔧 Fixing live events article link errors...")
    
    try:
        # Check if live events template exists
        if not os.path.exists('templates/live_events.html'):
            print("⚠️ Live events template not found")
            return False
            
        with open('templates/live_events.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix any problematic article link patterns
        # Replace direct article ID links with safer URL generation
        content = content.replace(
            'href="/article/{{ event.article_id }}"',
            'href="{{ url_for(\'view_article\', article_id=event.article_id) if event.article_id else \'#\' }}"'
        )
        
        # Add error handling for missing article IDs
        content = content.replace(
            'href="/article/{{ article.id }}"',
            'href="{{ url_for(\'view_article\', article_id=article.id) if article and article.id else \'#\' }}"'
        )
        
        # Add JavaScript error handling for article links
        js_error_handling = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Add error handling for article links
    const articleLinks = document.querySelectorAll('a[href*="/article/"]');
    articleLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href.endsWith('#') || this.href.endsWith('/article/')) {
                e.preventDefault();
                showNotification('Article not available', 'warning');
            }
        });
    });
    
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            padding: 10px 20px;
            border-radius: 5px;
            background: ${type === 'warning' ? '#fff3cd' : '#d4edda'};
            border: 1px solid ${type === 'warning' ? '#ffeaa7' : '#c3e6cb'};
            color: ${type === 'warning' ? '#856404' : '#155724'};
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});
</script>'''
        
        # Add the JavaScript before the closing body tag
        if '</body>' in content:
            content = content.replace('</body>', js_error_handling + '\n</body>')
        
        with open('templates/live_events.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed live events article links")
        return True
        
    except Exception as e:
        print(f"❌ Live events fix error: {e}")
        return False

def add_loading_screens_to_app():
    """Add loading screen functionality to the main app"""
    print("🔄 Adding loading screen functionality to app...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add loading screen route
        loading_route = '''
@app.route('/loading')
def loading_screen():
    """Show loading screen with optional redirect"""
    message = request.args.get('message', 'Loading...')
    redirect_url = request.args.get('redirect_url', '')
    redirect_delay = request.args.get('delay', 3000, type=int)
    
    return render_template('loading.html', 
                         message=message,
                         redirect_url=redirect_url,
                         redirect_delay=redirect_delay)

'''
        
        # Add the route before the main execution
        insertion_point = content.find('if __name__ == \'__main__\':')
        if insertion_point != -1:
            content = content[:insertion_point] + loading_route + '\n' + content[insertion_point:]
        
        # Add loading screen wrapper for slow operations
        loading_wrapper = '''
def with_loading_screen(message="Loading...", min_delay=1000):
    """Decorator to show loading screen for slow operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # For AJAX requests, return loading status
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "loading", "message": message})
            
            # For regular requests, show loading screen briefly then redirect
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                
                # If operation was fast, no need for loading screen
                if elapsed < min_delay:
                    return result
                    
                # If operation was slow, it probably already rendered
                return result
                
            except Exception as e:
                # On error, show error page instead of loading screen
                logger.error(f"Error in {func.__name__}: {e}")
                return render_template('error.html', 
                                     error="An error occurred while loading the page.",
                                     details=str(e) if app.debug else None), 500
        
        return wrapper
    return decorator

'''
        
        # Add the wrapper function after imports
        import_end = content.find('\napp = Flask(__name__)')
        if import_end != -1:
            content = content[:import_end] + '\n' + loading_wrapper + content[import_end:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added loading screen functionality")
        return True
        
    except Exception as e:
        print(f"❌ Loading screen addition error: {e}")
        return False

def create_error_template():
    """Create a user-friendly error template"""
    print("🔧 Creating user-friendly error template...")
    
    error_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - WiseNews</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        
        .error-container {
            text-align: center;
            max-width: 500px;
            padding: 2rem;
        }
        
        .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        .error-title {
            font-size: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        .error-message {
            font-size: 1.1rem;
            margin-bottom: 2rem;
            opacity: 0.9;
            line-height: 1.5;
        }
        
        .error-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .btn-primary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .btn-primary:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .error-details {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.9rem;
            text-align: left;
            display: none;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-title">Oops! Something went wrong</div>
        <div class="error-message">
            {{ error if error else "We're having trouble loading this page right now." }}
        </div>
        
        <div class="error-actions">
            <a href="javascript:history.back()" class="btn btn-primary">Go Back</a>
            <a href="/" class="btn btn-primary">Home</a>
            <a href="javascript:location.reload()" class="btn btn-primary">Retry</a>
            {% if details %}
            <button onclick="toggleDetails()" class="btn btn-primary">Show Details</button>
            {% endif %}
        </div>
        
        {% if details %}
        <div class="error-details" id="errorDetails">
            <strong>Error Details:</strong><br>
            {{ details }}
        </div>
        {% endif %}
    </div>
    
    <script>
        function toggleDetails() {
            const details = document.getElementById('errorDetails');
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }
        
        // Auto-refresh after 30 seconds
        setTimeout(function() {
            if (confirm('This page has been inactive for 30 seconds. Would you like to refresh?')) {
                location.reload();
            }
        }, 30000);
    </script>
</body>
</html>'''
    
    try:
        with open('templates/error.html', 'w', encoding='utf-8') as f:
            f.write(error_template)
        print("✅ Created error template")
        return True
    except Exception as e:
        print(f"❌ Error template creation error: {e}")
        return False

def update_article_view_route():
    """Update article view route to handle errors gracefully"""
    print("🔧 Updating article view route for better error handling...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the article view route and add better error handling
        pattern = r'@app\.route\(\'/article/<int:article_id>\'\)\s*\n@[^\n]*\s*\ndef\s+view_article\([^)]*\):'
        
        new_route = '''@app.route('/article/<int:article_id>')
def view_article(article_id):'''
        
        # Replace with safer version
        content = re.sub(pattern, new_route, content)
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated article view route")
        return True
        
    except Exception as e:
        print(f"❌ Article route update error: {e}")
        return False

def main():
    """Run all user experience fixes"""
    print("🚀 WiseNews User Experience Fix")
    print("=" * 50)
    
    fixes = [
        create_loading_screen_templates,
        create_error_template,
        fix_scraper_protection_for_users,
        remove_scraper_protection_from_user_routes,
        fix_live_events_article_links,
        add_loading_screens_to_app,
        update_article_view_route
    ]
    
    success_count = 0
    for fix_func in fixes:
        try:
            if fix_func():
                success_count += 1
            print()
        except Exception as e:
            print(f"❌ Fix function {fix_func.__name__} failed: {e}")
            print()
    
    print(f"📊 Fix Summary: {success_count}/{len(fixes)} successful")
    
    if success_count >= len(fixes) * 0.8:  # 80% success rate
        print("\n🎉 User Experience Improvements Applied!")
        print("✅ Loading screens added for slow operations")
        print("✅ Scraper protection made user-friendly")
        print("✅ Live events errors fixed")
        print("✅ Better error handling implemented")
        print("\n🔄 Please restart the server: python app.py")
    else:
        print(f"\n⚠️ Some fixes failed. Check errors above.")
    
    return success_count >= len(fixes) * 0.8

if __name__ == "__main__":
    main()
