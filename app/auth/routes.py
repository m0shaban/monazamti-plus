from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
import logging
import uuid
from app import db, limiter
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm
from app.auth import bp
from app.utils.security_monitoring import log_security_event, detect_suspicious_activity

# Configure logger
logger = logging.getLogger(__name__)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # More strict rate limiting for login attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        logger.info(f"Attempting login for email: {form.email.data}")
        user = User.query.filter_by(email=form.email.data).first()
        
        # Log the login attempt
        security_details = {
            'email': form.email.data,
            'remember_me': form.remember_me.data,
            'success': False,
            'reason': 'User not found' if not user else 'Invalid credentials'
        }
        
        # Add debug logging
        if user:
            logger.info(f"User found: {user.username}, validating password")
            password_valid = user.check_password(form.password.data)
            logger.info(f"Password valid: {password_valid}")
            
            # Update reason if user exists
            security_details['reason'] = 'Invalid credentials' if not password_valid else 'Success'
            security_details['success'] = password_valid
        else:
            logger.warning(f"No user found with email: {form.email.data}")
            
        if user and user.check_password(form.password.data):
            # Check for suspicious activity
            if detect_suspicious_activity(user.id, 'login'):
                log_security_event('suspicious_login', security_details, severity="WARNING")
                flash('Unusual account activity detected. Please contact support if you believe this is an error.', 'warning')
                return render_template('auth/login.html', form=form)
                
            login_user(user, remember=form.remember_me.data)
            logger.info(f"Login successful for user: {user.username}")
            
            # Update security log with successful login
            security_details['success'] = True
            security_details['reason'] = 'Success'
            log_security_event('login_success', security_details)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            logger.warning(f"Login failed for email: {form.email.data}")
            
            # Log failed login attempt
            log_security_event('login_failure', security_details, severity="WARNING")
            
            flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
@limiter.limit("5 per minute")  # Rate limiting for logout
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limiting for signup
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='user',
            fs_uniquifier=str(uuid.uuid4())
        )
        
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limiting for forgot password
def forgot_password():
    # Placeholder for password reset functionality
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # In a real application, send a password reset email here
            flash('If an account exists with this email, a password reset link has been sent.', 'info')
        else:
            # Don't reveal if email exists for security
            flash('If an account exists with this email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')
