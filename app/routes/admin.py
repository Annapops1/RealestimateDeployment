from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import User
from app.models.property import Property
from sqlalchemy import func
from app.extensions import db
from datetime import datetime
from app.models.property_document import PropertyDocument
from flask_mail import Message
from app.extensions import mail

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/')
@admin_required
def dashboard():
    # Count statistics
    total_users = User.query.count()
    total_properties = Property.query.count()
    verified_properties = Property.query.filter_by(is_verified=True).count()
    pending_properties = Property.query.filter_by(verification_status='pending').count()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          total_properties=total_properties,
                          verified_properties=verified_properties,
                          pending_properties=pending_properties)

@bp.route('/manage-users')
@admin_required
def manage_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/manage-properties')
@admin_required
def manage_properties():
    properties = Property.query.order_by(Property.created_at.desc()).all()
    return render_template('admin/manage_properties.html', properties=properties)

@bp.route('/user/<int:user_id>/toggle-admin')
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow admin to remove their own admin status
    if user.id == current_user.id:
        flash('You cannot remove your own admin status', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = "granted" if user.is_admin else "revoked"
    flash(f'Admin privileges {action} for {user.username}', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/user/<int:user_id>/toggle-active')
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    user.active = not user.active
    db.session.commit()
    
    action = "activated" if user.active else "deactivated"
    flash(f'User {user.username} has been {action}', 'success')
    return redirect(url_for('admin.manage_users'))

@bp.route('/property/<int:id>/verify', methods=['GET', 'POST'])
@admin_required
def verify_property(id):
    property = Property.query.get_or_404(id)
    
    # GET request - show the verification page with property details
    if request.method == 'GET':
        return render_template('admin/verify_property.html', property=property)
    
    # POST request - process the verification
    verification = request.form.get('verification')
    feedback = request.form.get('feedback')
    
    # Check if at least one document is verified
    has_verified_document = any(doc.is_verified for doc in property.documents)
    
    if verification == 'approve' and not has_verified_document and property.documents:
        flash('Cannot approve property without at least one verified document', 'danger')
        return redirect(url_for('admin.verify_property', id=id))
    
    if verification == 'approve':
        property.verification_status = 'approved'
        property.is_verified = True
    elif verification == 'reject':
        property.verification_status = 'rejected'
        property.is_verified = False
    
    property.admin_feedback = feedback
    property.verified_at = datetime.utcnow()
    property.verified_by = current_user.id
    
    db.session.commit()
    
    # Notify the seller
    seller = User.query.get(property.user_id)
    if seller:
        status = "approved" if property.is_verified else "rejected"
        msg = Message(
            f"Your property listing has been {status}",
            recipients=[seller.email]
        )
        msg.body = f"""
        Dear {seller.username},
        
        Your property listing "{property.title}" has been {status} by our admin team.
        
        {f"Feedback: {feedback}" if feedback else ""}
        
        Thank you for using our platform.
        
        Best regards,
        The RealEstiMate Team
        """
        mail.send(msg)
    
    flash(f'Property has been {verification}d', 'success')
    return redirect(url_for('admin.pending_properties'))

@bp.route('/property/<int:property_id>/reject', methods=['POST'])
@admin_required
def reject_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    feedback = request.form.get('feedback', '')
    
    property.is_verified = False
    property.verification_status = 'rejected'
    property.admin_feedback = feedback
    
    db.session.commit()
    
    flash(f'Property "{property.title}" has been rejected', 'success')
    return redirect(url_for('admin.manage_properties'))

@bp.route('/update_recommendations')
@admin_required
def update_recommendations():
    """Update the recommendation engine (admin only)"""
    from app.utils.recommendation_engine import recommendation_engine
    
    try:
        recommendation_engine.build_property_features()
        recommendation_engine.build_user_preferences()
        recommendation_engine.build_property_similarity_matrix()
        recommendation_engine.build_user_property_matrix()
        
        # Train matrix factorization model
        recommendation_engine.build_matrix_factorization_model()
        
        recommendation_engine.last_update = datetime.utcnow()
        
        flash('Recommendation engine updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating recommendation engine: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@bp.route('/document/<int:id>/verify', methods=['POST'])
@admin_required
def verify_document(id):
    document = PropertyDocument.query.get_or_404(id)
    property_id = document.property_id
    
    verification = request.form.get('verification')
    feedback = request.form.get('feedback')
    
    if verification == 'verify':
        document.is_verified = True
    else:
        document.is_verified = False
    
    document.admin_feedback = feedback
    document.verified_at = datetime.utcnow()
    document.verified_by = current_user.id
    
    db.session.commit()
    flash('Document verification status updated', 'success')
    
    return redirect(url_for('admin.verify_property', id=property_id))

@bp.route('/properties/pending')
@admin_required
def pending_properties():
    # Get all properties with pending verification status
    properties = Property.query.filter_by(verification_status='pending').order_by(Property.created_at.desc()).all()
    return render_template('admin/pending_properties.html', properties=properties) 