from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from bson import ObjectId
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # Use in-memory storage; replace with "redis://localhost:6379" for Redis
    default_limits=["200 per day", "50 per hour"]
)

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
        @limiter.limit(limit)
        def wrapped_function(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_function
    return decorator

from flask import current_app

def get_mongo_db():
    """Retrieve the MongoDB database connection from the Flask app context."""
    try:
        return current_app.mongo.db
    except AttributeError as e:
        current_app.logger.error(f"MongoDB not initialized: {str(e)}")
        raise Exception("MongoDB connection is not initialized in the application context")
