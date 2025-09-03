from flask import Blueprint, render_template

general_bp = Blueprint('general', __name__, template_folder='templates')

@general_bp.route('/landing')
def landing():
    """Landing page for new visitors"""
    return render_template('general/landingpage.html')

@general_bp.route('/about')
def about():
    """About page"""
    return render_template('general/about.html')

@general_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('general/contact.html')

@general_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('general/privacy.html')

@general_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('general/terms.html')