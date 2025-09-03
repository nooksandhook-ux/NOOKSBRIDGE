from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from bson import ObjectId

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        user = current_app.mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or not user.get('is_admin', False):
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limit):
    """Custom decorator to apply rate limiting to specific routes"""
    def decorator(f):
        @wraps(f)
        @current_app.limiter.limit(limit)  # Use current_app.limiter
        def wrapped_function(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_function
    return decorator

def get_mongo_db():
    """Retrieve the MongoDB database connection from the Flask app context."""
    try:
        return current_app.mongo.db
    except AttributeError as e:
        current_app.logger.error(f"MongoDB not initialized: {str(e)}")
        raise Exception("MongoDB connection is not initialized in the application context")

