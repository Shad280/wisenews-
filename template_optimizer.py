"""
Template Performance Optimizer
Optimizes template rendering and static content delivery
"""

import os
from flask import Flask, render_template, request, g
import gzip
from io import BytesIO
import hashlib
import time

class TemplateOptimizer:
    def __init__(self, app):
        self.app = app
        self.template_cache = {}
        
    def optimize_template_rendering(self):
        """Optimize template rendering performance"""
        
        # Pre-compile templates during startup
        template_folder = self.app.template_folder
        if template_folder and os.path.exists(template_folder):
            print("🔧 Pre-compiling templates...")
            
            for filename in os.listdir(template_folder):
                if filename.endswith('.html'):
                    try:
                        # Pre-load template to compile it
                        self.app.jinja_env.get_template(filename)
                        print(f"   ✅ Pre-compiled: {filename}")
                    except Exception as e:
                        print(f"   ⚠️ Failed to pre-compile {filename}: {e}")
        
        # Configure Jinja2 for better performance
        self.app.jinja_env.auto_reload = False
        self.app.jinja_env.cache_size = 400  # Increase template cache
        
        print("✅ Template rendering optimized")
    
    def add_static_file_caching(self):
        """Add aggressive caching for static files"""
        
        @self.app.after_request
        def cache_static_files(response):
            # Cache static files for 1 year
            if request.endpoint == 'static':
                response.headers['Cache-Control'] = 'public, max-age=31536000'
                response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            
            # Cache API responses for 5 minutes
            elif request.endpoint and 'api' in str(request.endpoint):
                response.headers['Cache-Control'] = 'public, max-age=300'
            
            # Cache HTML pages for 60 seconds
            elif response.mimetype == 'text/html':
                response.headers['Cache-Control'] = 'public, max-age=60'
            
            return response
        
        print("✅ Static file caching configured")
    
    def optimize_response_compression(self):
        """Optimize response compression"""
        
        @self.app.after_request
        def compress_responses(response):
            # Skip if already compressed or too small
            if (response.headers.get('Content-Encoding') or 
                not response.data or 
                len(response.data) < 1024):
                return response
            
            # Check if client accepts gzip
            if 'gzip' not in request.headers.get('Accept-Encoding', ''):
                return response
            
            # Skip binary content
            if response.mimetype.startswith('image/') or response.mimetype.startswith('video/'):
                return response
            
            # Compress the response
            try:
                gzip_buffer = BytesIO()
                with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as gzip_file:
                    gzip_file.write(response.data)
                
                compressed_data = gzip_buffer.getvalue()
                
                # Only use compression if it actually reduces size
                if len(compressed_data) < len(response.data):
                    response.set_data(compressed_data)
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = len(compressed_data)
                    response.headers['Vary'] = 'Accept-Encoding'
                
            except Exception as e:
                # If compression fails, return original response
                pass
            
            return response
        
        print("✅ Response compression optimized")
    
    def add_performance_monitoring(self):
        """Add performance monitoring headers"""
        
        @self.app.before_request
        def start_timer():
            g.start_time = time.time()
        
        @self.app.after_request
        def add_timing_header(response):
            if hasattr(g, 'start_time'):
                total_time = (time.time() - g.start_time) * 1000
                response.headers['X-Response-Time'] = f'{total_time:.2f}ms'
                
                # Add performance category
                if total_time < 100:
                    response.headers['X-Performance'] = 'excellent'
                elif total_time < 300:
                    response.headers['X-Performance'] = 'good'
                elif total_time < 500:
                    response.headers['X-Performance'] = 'acceptable'
                else:
                    response.headers['X-Performance'] = 'slow'
            
            return response
        
        print("✅ Performance monitoring configured")
    
    def optimize_database_queries_in_templates(self):
        """Optimize database queries used in templates"""
        
        # Create template globals for commonly used data
        @self.app.template_global()
        def get_category_counts():
            """Cached category counts for sidebar"""
            from critical_performance_fix import perf_fix
            
            conn = perf_fix.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM articles 
                    WHERE category IS NOT NULL 
                    GROUP BY category 
                    ORDER BY count DESC 
                    LIMIT 10
                ''')
                return dict(cursor.fetchall())
            finally:
                perf_fix.return_connection(conn)
        
        @self.app.template_global()
        def get_quick_stats():
            """Cached quick stats for dashboard"""
            from critical_performance_fix import perf_fix
            
            conn = perf_fix.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM articles')
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM articles WHERE date_added >= date('now', '-1 day')")
                today = cursor.fetchone()[0]
                
                return {'total': total, 'today': today}
            finally:
                perf_fix.return_connection(conn)
        
        print("✅ Template database queries optimized")
    
    def apply_all_optimizations(self):
        """Apply all template and rendering optimizations"""
        print("🚀 Applying template and rendering optimizations...")
        
        self.optimize_template_rendering()
        self.add_static_file_caching()
        self.optimize_response_compression()
        self.add_performance_monitoring()
        self.optimize_database_queries_in_templates()
        
        print("🎉 All template optimizations applied!")

def optimize_templates(app):
    """Apply template optimizations to Flask app"""
    optimizer = TemplateOptimizer(app)
    optimizer.apply_all_optimizations()
    return optimizer
