import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user, login_user
from app import db
from app.utils.validators import validate_phone, validate_pincode
from app.utils.constants import INDIAN_STATES
from app.models.property import Property
from app.models.wishlist import Wishlist
from app.models.interest import PropertyInterest
from app.models.contract import Contract
from datetime import datetime
from flask_dance.contrib.google import google
from app.models.user import User
from app.models.oauth import OAuth
from app.utils.recommendation_engine import recommendation_engine


bp = Blueprint('user', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'seller':
        return redirect(url_for('user.seller_dashboard'))
    
    # Get states for dropdown
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", 
        "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", 
        "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", 
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
        "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh", 
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh", 
        "Lakshadweep", "Puducherry"
    ]
    
    # Get user's property interests
    interests = PropertyInterest.query.filter_by(buyer_id=current_user.id).all()
    
    # For recommendations, let's use the user's built-in method which handles this properly
    recommendations = current_user.get_recommended_properties(limit=5)
    
    return render_template('user/dashboard.html', 
                          states=states, 
                          interests=interests,
                          recommendations=recommendations)

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    phone_number = request.form.get('phone_number')
    zip_code = request.form.get('zip_code')
    
    # Validate phone number
    if phone_number and not validate_phone(phone_number):
        flash('Please enter a valid Indian phone number', 'danger')
        return redirect(url_for('user.dashboard'))
        
    # Validate PIN code
    if zip_code and not validate_pincode(zip_code):
        flash('Please enter a valid 6-digit PIN code', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Update user profile information
    current_user.phone_number = phone_number
    current_user.address = request.form.get('address')
    current_user.city = request.form.get('city')
    current_user.state = request.form.get('state')
    current_user.zip_code = zip_code
    
    # Update preferences
    current_user.preferred_property_type = request.form.get('preferred_property_type')
    current_user.preferred_location = request.form.get('preferred_location')
    current_user.preferred_latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
    current_user.preferred_longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
    
    # Update proximity preference for buyers
    if current_user.user_type == 'buyer':
        try:
            proximity = float(request.form.get('preferred_proximity', 10.0))
            current_user.preferred_proximity = min(max(proximity, 1.0), 50.0)  # Limit between 1-50km
        except ValueError:
            current_user.preferred_proximity = 10.0  # Default if invalid input
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('user.dashboard'))

@bp.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if current_user.user_type != 'seller':
        return redirect(url_for('user.dashboard'))
    properties = Property.query.filter_by(user_id=current_user.id).order_by(Property.created_at.desc()).all()
    return render_template('user/seller_dashboard.html', properties=properties)

@bp.route('/seller/profile', methods=['GET', 'POST'])
@login_required
def seller_profile():
    if current_user.user_type != 'seller':
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        zip_code = request.form.get('zip_code')
        
        # Validate phone number
        if phone_number and not validate_phone(phone_number):
            flash('Please enter a valid Indian phone number', 'danger')
            return redirect(url_for('user.seller_profile'))
            
        # Validate PIN code
        if zip_code and not validate_pincode(zip_code):
            flash('Please enter a valid 6-digit PIN code', 'danger')
            return redirect(url_for('user.seller_profile'))
        
        current_user.company_name = request.form.get('company_name')
        current_user.license_number = request.form.get('license_number')
        current_user.phone_number = phone_number
        current_user.address = request.form.get('address')
        current_user.city = request.form.get('city')
        current_user.state = request.form.get('state')
        current_user.zip_code = zip_code
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.seller_dashboard'))
        
    return render_template('user/seller_profile.html', states=INDIAN_STATES)

@bp.route('/wishlist/add/<int:property_id>')
@login_required
def add_to_wishlist(property_id):
    if current_user.user_type != 'buyer':
        flash('Only buyers can add properties to wishlist', 'danger')
        return redirect(url_for('property.details', id=property_id))
        
    property = Property.query.get_or_404(property_id)
    
    # Check if already in wishlist
    if Wishlist.query.filter_by(user_id=current_user.id, property_id=property_id).first():
        flash('Property already in wishlist', 'info')
        return redirect(url_for('property.details', id=property_id))
    
    wishlist_item = Wishlist(user_id=current_user.id, property_id=property_id)
    db.session.add(wishlist_item)
    db.session.commit()
    
    flash('Property added to wishlist', 'success')
    return redirect(url_for('property.details', id=property_id))

@bp.route('/wishlist/remove/<int:property_id>')
@login_required
def remove_from_wishlist(property_id):
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id, 
        property_id=property_id
    ).first_or_404()
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    flash('Property removed from wishlist', 'success')
    return redirect(url_for('user.wishlist'))

@bp.route('/wishlist')
@login_required
def wishlist():
    if current_user.user_type != 'buyer':
        return redirect(url_for('user.dashboard'))
        
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id)\
        .order_by(Wishlist.created_at.desc()).all()
    return render_template('user/wishlist.html', wishlist_items=wishlist_items)

@bp.route('/seller/interests')
@login_required
def view_interests():
    if current_user.user_type != 'seller':
        return redirect(url_for('user.dashboard'))
        
    interests = PropertyInterest.query.join(Property).filter(
        Property.user_id == current_user.id
    ).order_by(PropertyInterest.created_at.desc()).all()
    
    # Mark interests as read
    for interest in interests:
        if not interest.is_read:
            interest.is_read = True
    db.session.commit()
    
    return render_template('user/interests.html', interests=interests)

@bp.route('/my-properties')
@login_required
def my_properties():
    if current_user.user_type != 'buyer':
        flash('Only buyers can access this page', 'danger')
        return redirect(url_for('main.index'))
    
    now = datetime.utcnow()
    
    # Get contracts where user is buyer and payment is made
    purchased_properties = Contract.query.filter(
        Contract.buyer_id == current_user.id,
        Contract.advance_payment_made == True
    ).all()
    
    return render_template('user/my_properties.html', 
                         purchased_properties=purchased_properties,
                         now=now)

@bp.route('/google-authorized')
def google_authorized():
    if not google.authorized:
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    resp = google.get('/oauth2/v1/userinfo')
    if not resp.ok:
        flash('Failed to get user info from Google.', 'danger')
        return redirect(url_for('auth.login'))
    
    google_info = resp.json()
    google_email = google_info.get('email')
    
    # Find user by email
    user = User.query.filter_by(email=google_email).first()
    
    if user:
        # Check if user is active
        if hasattr(user, 'active') and user.active is not None and not user.active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        flash('Successfully logged in with Google!', 'success')
        return redirect(url_for('main.index'))
    else:
        # Create new user
        username = google_info.get('name', '').replace(' ', '_').lower()
        base_username = username
        counter = 1
        
        # Ensure username is unique
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=google_email,
            active=True  # Explicitly set active to True for new users
        )
        
        # Generate a random password for the user
        import secrets
        import string
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created with Google! Please complete your profile.', 'success')
        return redirect(url_for('user.complete_profile'))

@bp.route('/login')
def login():
    if google.authorized:
        return redirect(url_for('user.google_authorized'))
    return redirect(url_for('google.login'))

@bp.route('/complete_profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Only redirect buyers if profile is complete
    if current_user.is_profile_complete() and current_user.user_type == 'buyer':
        return redirect(url_for('user.dashboard'))
    
    # For sellers, we'll still show the form but won't force them to complete it

    if request.method == 'POST':
        user_type = request.form.get('user_type')
        if user_type not in ['buyer', 'seller']:
            flash('Invalid user type selected', 'danger')
            return redirect(url_for('user.complete_profile'))
        
        current_user.user_type = user_type
        current_user.phone_number = request.form.get('phone_number')
        current_user.address = request.form.get('address')
        current_user.city = request.form.get('city')
        current_user.state = request.form.get('state')
        
        if user_type == 'seller':
            current_user.company_name = request.form.get('company_name')
            current_user.license_number = request.form.get('license_number')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        
        if user_type == 'seller':
            return redirect(url_for('user.seller_dashboard'))
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/complete_profile.html', states=INDIAN_STATES)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # ... existing profile update code ...
        
        # Update proximity preference for buyers
        if current_user.user_type == 'buyer':
            try:
                proximity = float(request.form.get('preferred_proximity', 10.0))
                current_user.preferred_proximity = min(max(proximity, 1.0), 50.0)  # Limit between 1-50km
            except ValueError:
                current_user.preferred_proximity = 10.0  # Default if invalid input
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.dashboard'))

@bp.route('/interests')
@login_required
def interests():
    """Display the buyer's property interests"""
    if current_user.user_type != 'buyer':
        flash('This page is only available to buyers', 'warning')
        return redirect(url_for('main.index'))
    
    # Get user's property interests with the associated properties
    interests = PropertyInterest.query.filter_by(buyer_id=current_user.id).all()
    
    return render_template('user/interests.html', interests=interests)

