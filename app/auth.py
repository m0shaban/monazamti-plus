from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash  # added password check import
from app.models import User
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # ...existing authentication logic...
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        # Verify password using check_password_hash
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password', 'danger')  # adjust message here if needed
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
