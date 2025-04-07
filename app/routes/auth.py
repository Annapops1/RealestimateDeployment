from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from app import db
from app.utils.validators import validate_email, validate_password, validate_username
import re

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user is active - handle NULL values
            if hasattr(user, 'active') and user.active is not None and not user.active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=request.form.get('remember_me'))
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not validate_username(username):
            flash('Username must be 5-30 characters long and can only contain letters, numbers, and underscores', 'danger')
            return render_template('auth/register.html')
            
        if not validate_email(email):
            flash('Please enter a valid email address', 'danger')
            return render_template('auth/register.html')
            
        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, number and special character', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('auth/register.html')
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/seller/register', methods=['GET', 'POST'])
def seller_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        company_name = request.form.get('company_name')
        license_number = request.form.get('license_number')
        
        # Validate username
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        # Validate password strength
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        # Check existing username/email
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        # Validate company name and license number if provided
        if company_name and (len(company_name) < 3 or len(company_name) > 100):
            flash('Company name should be between 3 and 100 characters', 'danger')
            return redirect(url_for('auth.seller_register'))
            
        if license_number and (len(license_number) < 5 or len(license_number) > 50):
            flash('License number should be between 5 and 50 characters', 'danger')
            return redirect(url_for('auth.seller_register'))

        user = User(
            username=username,
            email=email,
            user_type='seller',
            company_name=company_name,
            license_number=license_number
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/seller_register.html') 