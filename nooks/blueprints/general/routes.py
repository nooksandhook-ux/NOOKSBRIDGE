from flask import Blueprint, render_template, redirect, url_for, flash, session, request, make_response
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFError
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from jinja2.exceptions import TemplateNotFound
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from models import FeedbackManager
from flask import current_app
from utils.decorators import rate_limit

# Exempt crawlers from rate limiting
def exempt_crawlers():
    user_agent = request.user_agent.string
    return user_agent.startswith("facebookexternalhit") or \
           user_agent.startswith("Mozilla/5.0+(compatible; UptimeRobot")

# Define FeedbackForm class
class FeedbackForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    message = TextAreaField('Feedback', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Submit Feedback')

general_bp = Blueprint('general_bp', __name__, url_prefix='/')

@general_bp.route('/')
@limiter.limit("500 per minute", exempt_when=exempt_crawlers)
def landing():
    """Render the public landing page."""
    try:
        current_app.logger.info(
            f"Accessing landing page - Session: {dict(session)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        explore_features = [
            {'title': 'Reading Tracker', 'description': 'Track your books and reading progress with ease.', 'icon': 'bi bi-book'},
            {'title': 'Productivity Timer', 'description': 'Boost focus with customizable Pomodoro timers.', 'icon': 'bi bi-stopwatch'},
            {'title': 'Earn Rewards', 'description': 'Submit quotes from books to earn ₦10 per verified quote.', 'icon': 'bi bi-coin'}
        ]
        response = make_response(render_template(
            'general/landingpage.html',
            title='Welcome to Nook & Hook',
            explore_features=explore_features
        ))
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except TemplateNotFound as e:
        current_app.logger.error(
            f"Template not found: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        flash('An error occurred', 'danger')
        return render_template(
            'error/404.html',
            error_message="Unable to load the landing page due to a missing template.",
            title='Welcome to Nook & Hook'
        ), 404
    except Exception as e:
        current_app.logger.error(
            f"Error rendering landing page: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        flash('An error occurred', 'danger')
        return render_template(
            'error/500.html',
            error_message="Unable to load the landing page due to an internal error.",
            title='Welcome to Nook & Hook'
        ), 500

@general_bp.route('/about')
@limiter.limit("500 per minute", exempt_when=exempt_crawlers)
def about():
    """Render the public about page."""
    try:
        return render_template(
            'general/about.html',
            title='About Nook & Hook'
        )
    except TemplateNotFound as e:
        current_app.logger.error(
            f"Template not found: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        return render_template(
            'error/404.html',
            error=str(e),
            title='About Nook & Hook'
        ), 404

@general_bp.route('/contact')
@limiter.limit("500 per minute", exempt_when=exempt_crawlers)
def contact():
    """Render the public contact page."""
    try:
        return render_template(
            'general/contact.html',
            title='Contact Us'
        )
    except TemplateNotFound as e:
        current_app.logger.error(
            f"Template not found: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        return render_template(
            'error/404.html',
            error=str(e),
            title='Contact Us'
        ), 404

@general_bp.route('/feedback', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def feedback():
    """Render the public feedback page and handle form submission."""
    form = FeedbackForm()
    current_app.logger.info(
        'Handling feedback',
        extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous', 'ip_address': request.remote_addr}
    )

    if request.method == 'POST' and form.validate_on_submit():
        try:
            name = form.name.data
            email = form.email.data
            message = utils.sanitize_input(form.message.data.strip(), max_length=1000)

            with current_app.app_context():
                db = get_mongo_db()
                feedback_entry = {
                    'name': name,
                    'email': email,
                    'message': message,
                    'timestamp': datetime.now(timezone.utc),
                    'session_id': session.get('sid', 'no-session-id')
                }
                create_feedback(db, feedback_entry)
                
                db.audit_logs.insert_one({
                    'admin_id': 'system',
                    'action': 'submit_feedback',
                    'details': {
                        'name': name,
                        'email': email
                    },
                    'timestamp': datetime.now(timezone.utc)
                })

            current_app.logger.info(
                f'Feedback submitted: name={name}, email={email}',
                extra={'session_id': session.get('sid', 'no-session-id'), 'ip_address': request.remote_addr}
            )
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('general_bp.landing'))
        except CSRFError as e:
            current_app.logger.error(
                f'CSRF error in feedback submission: {str(e)}',
                extra={'session_id': session.get('sid', 'no-session-id'), 'ip_address': request.remote_addr}
            )
            flash('Invalid CSRF token. Please try again.', 'danger')
            return render_template('general/feedback.html', form=form, title='Feedback'), 400
        except Exception as e:
            current_app.logger.error(
                f'Error processing feedback: {str(e)}',
                extra={'session_id': session.get('sid', 'no-session-id'), 'ip_address': request.remote_addr}
            )
            flash('Error occurred during feedback submission', 'danger')
            return render_template('general/feedback.html', form=form, title='Feedback'), 500

    return render_template('general/feedback.html', form=form, title='Feedback')

@general_bp.route('/privacy')
@limiter.limit("500 per minute", exempt_when=exempt_crawlers)
def privacy():
    """Render the public privacy policy page."""
    try:
        return render_template(
            'general/privacy.html',
            title='Privacy Policy'
        )
    except TemplateNotFound as e:
        current_app.logger.error(
            f"Template not found: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        return render_template(
            'error/404.html',
            error=str(e),
            title='Privacy Policy'
        ), 404

@general_bp.route('/terms')
@limiter.limit("500 per minute", exempt_when=exempt_crawlers)
def terms():
    """Render the public terms of service page."""
    try:
        return render_template(
            'general/terms.html',
            title='Terms of Service'
        )
    except TemplateNotFound as e:
        current_app.logger.error(
            f"Template not found: {str(e)}",
            extra={'session_id': session.get('sid', 'no-session-id'), 'user_id': 'anonymous'}
        )
        return render_template(
            'error/404.html',
            error=str(e),
            title='Terms of Service'
        ), 404
