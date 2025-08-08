
# Add this error handling wrapper to support_routes.py
def handle_db_errors(f):
    """Decorator to handle database errors gracefully"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                return jsonify({'error': 'Service temporarily unavailable. Please try again.'}), 503
            else:
                return jsonify({'error': 'Database error occurred.'}), 500
        except Exception as e:
            return jsonify({'error': 'An unexpected error occurred.'}), 500
    
    return decorated_function
