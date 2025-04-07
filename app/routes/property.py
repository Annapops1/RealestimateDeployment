from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.property import Property
from app.models.interest import PropertyInterest
from app.utils.image_handler import save_property_image
from datetime import datetime
from flask import current_app
from flask_mail import Message
from app import mail
from app.models.wishlist import Wishlist
from app.models.user import User
from app.models.contract import Contract
from app.models.property_image import PropertyImage
from app.utils.document_handler import save_property_document
from app.models.property_document import PropertyDocument

bp = Blueprint('property', __name__)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.user_type != 'seller':
        flash('Only sellers can add properties', 'danger')
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        property = Property(
            title=request.form.get('title'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            property_type=request.form.get('property_type'),
            location=request.form.get('location'),
            latitude=float(request.form.get('latitude')) if request.form.get('latitude') else None,
            longitude=float(request.form.get('longitude')) if request.form.get('longitude') else None,
            area=float(request.form.get('area')),
            bedrooms=int(request.form.get('bedrooms')) if request.form.get('bedrooms') else None,
            bathrooms=int(request.form.get('bathrooms')) if request.form.get('bathrooms') else None,
            total_floors=int(request.form.get('total_floors')) if request.form.get('total_floors') else None,
            user_id=current_user.id,
            verification_status='pending',
            is_verified=False
        )
        
        db.session.add(property)
        db.session.flush()  # Get the property ID without committing
        
        # Handle multiple image uploads
        images = request.files.getlist('property_images')
        is_first_image = True
        
        for image in images:
            if image and image.filename:
                image_filename, image_url = save_property_image(image)
                if image_filename and image_url:
                    property_image = PropertyImage(
                        property_id=property.id,
                        filename=image_filename,
                        url=image_url,
                        is_primary=is_first_image  # First image is primary
                    )
                    db.session.add(property_image)
                    is_first_image = False
        
        # Handle document upload
        document_file = request.files.get('property_document')
        document_type = request.form.get('document_type')
        
        if document_file and document_file.filename and document_type:
            document_filename, document_url = save_property_document(document_file)
            if document_filename and document_url:
                property_document = PropertyDocument(
                    property_id=property.id,
                    filename=document_filename,
                    url=document_url,
                    document_type=document_type,
                    is_verified=False
                )
                db.session.add(property_document)
        
        db.session.commit()
        flash('Property added successfully! It will be visible after admin verification.', 'success')
        return redirect(url_for('user.seller_dashboard'))
        
    return render_template('property/add.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    property = Property.query.get_or_404(id)
    if property.user_id != current_user.id:
        flash('You can only edit your own properties', 'danger')
        return redirect(url_for('user.seller_dashboard'))
        
    if request.method == 'POST':
        property.title = request.form.get('title')
        property.description = request.form.get('description')
        property.price = float(request.form.get('price'))
        property.property_type = request.form.get('property_type')
        property.location = request.form.get('location')
        property.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
        property.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
        property.area = float(request.form.get('area'))
        property.bedrooms = int(request.form.get('bedrooms')) if request.form.get('bedrooms') else None
        property.bathrooms = int(request.form.get('bathrooms')) if request.form.get('bathrooms') else None
        property.total_floors = int(request.form.get('total_floors')) if request.form.get('total_floors') else None
        
        # Handle multiple image uploads (only if files are provided)
        images = request.files.getlist('property_images')
        for image in images:
            if image and image.filename:
                image_filename, image_url = save_property_image(image)
                if image_filename and image_url:
                    # Check if this is the first image for the property
                    is_first = len(property.images) == 0
                    property_image = PropertyImage(
                        property_id=property.id,
                        filename=image_filename,
                        url=image_url,
                        is_primary=is_first
                    )
                    db.session.add(property_image)
        
        # Handle document upload (only if a file is provided)
        document_file = request.files.get('property_document')
        if document_file and document_file.filename:
            document_filename, document_url = save_property_document(document_file)
            if document_filename and document_url:
                property_document = PropertyDocument(
                    property_id=property.id,
                    filename=document_filename,
                    url=document_url,
                    document_type='ownership',  # Default type
                    is_verified=False
                )
                db.session.add(property_document)
        
        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('property.details', id=property.id))
        
    return render_template('property/edit.html', property=property)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    property = Property.query.get_or_404(id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to delete this property', 'danger')
        return redirect(url_for('user.seller_dashboard'))
    
    # Check if property has any active contracts
    active_contracts = Contract.query.filter(
        Contract.property_id == property.id,
        Contract.status.in_(['pending', 'active', 'approved'])
    ).count()
    
    if active_contracts > 0:
        flash('Cannot delete property with active contracts. Please cancel all contracts first.', 'danger')
        return redirect(url_for('user.seller_dashboard'))
    
    # Get all users who have shown interest before deleting
    interested_users = User.query.join(PropertyInterest).filter(
        PropertyInterest.property_id == property.id
    ).all()
    
    # Get property details for email
    property_title = property.title
    property_location = property.location
    
    # Delete related interests
    PropertyInterest.query.filter_by(property_id=id).delete()
    
    # Delete from wishlists
    Wishlist.query.filter_by(property_id=id).delete()
    
    # Delete the property
    db.session.delete(property)
    db.session.commit()
    
    # Send emails to interested users
    for user in interested_users:
        try:
            send_property_deletion_email(user, property_title, property_location)
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {user.email}: {str(e)}")
    
    flash('Property has been deleted successfully', 'success')
    return redirect(url_for('user.seller_dashboard'))

def send_property_deletion_email(user, property_title, property_location):
    """Send email notification about property deletion"""
    subject = "Property Listing Removed - RealEstimate"
    
    # Get the sender email with a fallback
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME', 'noreply@realestimate.com'))
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        sender=sender
    )
    
    msg.body = f"""Dear {user.username},

We wanted to inform you that a property you were interested in has been removed from our listings.

Property Details:
- Title: {property_title}
- Location: {property_location}

This property is no longer available for viewing or purchase. We apologize for any inconvenience this may cause.

You can browse other similar properties on our platform.

Best regards,
The RealEstimate Team
"""

    msg.html = f"""
<p>Dear {user.username},</p>

<p>We wanted to inform you that a property you were interested in has been removed from our listings.</p>

<p><strong>Property Details:</strong><br>
- Title: {property_title}<br>
- Location: {property_location}</p>

<p>This property is no longer available for viewing or purchase. We apologize for any inconvenience this may cause.</p>

<p>You can browse other similar properties on our platform.</p>

<p>Best regards,<br>
The RealEstimate Team</p>
"""
    
    try:
        mail.send(msg)
    except Exception as e:
        # Log the error but don't crash the application
        current_app.logger.error(f"Failed to send email: {str(e)}")

@bp.route('/listings')
def listings():
    # Get filter parameters
    property_type = request.args.get('property_type')
    location = request.args.get('location')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    bedrooms = request.args.get('bedrooms')
    
    # Start with base query including verification filters
    query = Property.query.filter_by(
        is_available=True,
        is_verified=True,
        verification_status='approved'
    )
    
    # Apply additional filters
    if property_type:
        query = query.filter_by(property_type=property_type)
    if location:
        query = query.filter(Property.location.ilike(f'%{location}%'))
    if min_price:
        query = query.filter(Property.price >= float(min_price))
    if max_price:
        query = query.filter(Property.price <= float(max_price))
    if bedrooms:
        query = query.filter(Property.bedrooms >= int(bedrooms))
        
    properties = query.order_by(Property.created_at.desc()).all()
    
    return render_template('property/listings.html', properties=properties)

@bp.route('/details/<int:id>')
def details(id):
    property = Property.query.get_or_404(id)
    
    # Check if property has an active contract and user is not the seller or buyer
    has_contract = Contract.query.filter(
        Contract.property_id == property.id,
        Contract.status.in_(['pending', 'active', 'approved'])
    ).first()
    
    if has_contract and current_user.is_authenticated:
        # Allow seller and buyer to view the property
        if property.user_id != current_user.id and has_contract.buyer_id != current_user.id:
            flash('This property is currently under contract and not available for viewing.', 'warning')
            return redirect(url_for('main.index'))
    
    # Only allow access to approved properties unless user is admin or property owner
    if not property.is_verified or property.verification_status != 'approved':
        if not current_user.is_authenticated or \
           (not current_user.is_admin and current_user.id != property.user_id):
            flash('This property is not available for viewing', 'danger')
            return redirect(url_for('main.index'))
    
    return render_template('property/details.html', 
                         property=property,
                         google_maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY'])

@bp.route('/show-interest/<int:id>', methods=['POST'])
@login_required
def show_interest(id):
    if current_user.user_type != 'buyer':
        flash('Only buyers can show interest in properties', 'danger')
        return redirect(url_for('property.details', id=id))
        
    property = Property.query.get_or_404(id)
    message = request.form.get('message', '').strip()
    
    existing_interest = PropertyInterest.query.filter_by(
        property_id=id,
        buyer_id=current_user.id
    ).first()
    
    if existing_interest:
        flash('You have already shown interest in this property', 'info')
    else:
        # Create new interest
        interest = PropertyInterest(
            property_id=id,
            buyer_id=current_user.id,
            message=message
        )
        db.session.add(interest)
        
        # Remove from wishlist if it exists there
        if property in current_user.wishlisted_properties:
            current_user.wishlisted_properties.remove(property)
            flash('Property has been removed from your wishlist and added to interests', 'info')
        else:
            flash('Your interest has been sent to the seller', 'success')
            
        db.session.commit()
    
    return redirect(url_for('property.details', id=id))

# New admin routes for property verification
@bp.route('/admin/verify/<int:id>', methods=['GET', 'POST'])
@login_required
def verify_property(id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
        
    property = Property.query.get_or_404(id)
    
    if request.method == 'POST':
        status = request.form.get('status')
        if status not in ['approved', 'rejected']:
            flash('Invalid verification status', 'danger')
            return redirect(url_for('property.verify_property', id=id))
            
        property.verification_status = status
        property.is_verified = (status == 'approved')
        property.admin_feedback = request.form.get('feedback')
        property.verified_at = datetime.utcnow()
        property.verified_by = current_user.id
        
        db.session.commit()
        flash(f'Property {status}!', 'success')
        return redirect(url_for('admin.pending_properties'))
        
    return render_template('admin/verify_property.html', property=property)

@bp.route('/search')
def search():
    # Get search parameters
    query = request.args.get('query', '')
    property_type = request.args.get('property_type', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    
    # Build the base query
    properties_query = Property.query.filter(
        Property.is_available == True,
        Property.is_verified == True,
        Property.verification_status == 'approved',
        # Exclude properties with contracts
        ~Property.id.in_(
            db.session.query(Contract.property_id).filter(
                Contract.status.in_(['pending', 'active', 'approved'])
            )
        )
    )
    
    # Apply filters
    if query:
        properties_query = properties_query.filter(
            db.or_(
                Property.title.ilike(f'%{query}%'),
                Property.description.ilike(f'%{query}%'),
                Property.location.ilike(f'%{query}%')
            )
        )
    
    if property_type:
        properties_query = properties_query.filter(Property.property_type == property_type)
    
    if min_price:
        properties_query = properties_query.filter(Property.price >= float(min_price))
    
    if max_price:
        properties_query = properties_query.filter(Property.price <= float(max_price))
    
    # Execute query
    properties = properties_query.order_by(Property.created_at.desc()).all()
    
    return render_template('property/search.html', 
                          properties=properties, 
                          query=query,
                          property_type=property_type,
                          min_price=min_price,
                          max_price=max_price)

@bp.route('/remove-interest/<int:id>')
@login_required
def remove_interest(id):
    property = Property.query.get_or_404(id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to remove interests for this property', 'danger')
        return redirect(url_for('user.seller_dashboard'))
    
    # Check if property has any active contracts
    has_contract = Contract.query.filter(
        Contract.property_id == property.id,
        Contract.status.in_(['pending', 'active', 'approved'])
    ).first()
    
    if has_contract:
        flash('Cannot remove interests for a property with active contracts', 'danger')
        return redirect(url_for('user.seller_dashboard'))
    
    # Get all users who have shown interest
    interested_users = User.query.join(PropertyInterest).filter(
        PropertyInterest.property_id == property.id
    ).all()
    
    # Get property details for email
    property_title = property.title
    property_location = property.location
    
    # Delete related chats and messages
    from app.models.chat import Chat, ChatMessage
    
    # Get all chats related to this property
    chats = Chat.query.filter_by(property_id=property.id).all()
    
    # Delete all messages in these chats
    for chat in chats:
        ChatMessage.query.filter_by(chat_id=chat.id).delete()
    
    # Delete the chats
    for chat in chats:
        db.session.delete(chat)
    
    # Delete related interests
    PropertyInterest.query.filter_by(property_id=id).delete()
    
    db.session.commit()
    
    # Send emails to interested users
    for user in interested_users:
        send_interest_removal_email(user, property_title, property_location)
    
    flash('All interests and chats for this property have been removed successfully', 'success')
    return redirect(url_for('user.seller_dashboard'))

def send_interest_removal_email(user, property_title, property_location):
    """Send email notification about interest removal"""
    subject = "Property Interest Removed - RealEstimate"
    
    # Get the sender email with a fallback
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME', 'noreply@realestimate.com'))
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        sender=sender
    )
    
    msg.body = f"""Dear {user.username},

We wanted to inform you that your interest in a property has been removed by the seller.

Property Details:
- Title: {property_title}
- Location: {property_location}

This property is still available for viewing, but your previous interest and chat history have been removed.

You can browse other similar properties on our platform.

Best regards,
The RealEstimate Team
"""

    msg.html = f"""
<p>Dear {user.username},</p>

<p>We wanted to inform you that your interest in a property has been removed by the seller.</p>

<p><strong>Property Details:</strong><br>
- Title: {property_title}<br>
- Location: {property_location}</p>

<p>This property is still available for viewing, but your previous interest and chat history have been removed.</p>

<p>You can browse other similar properties on our platform.</p>

<p>Best regards,<br>
The RealEstimate Team</p>
"""
    
    try:
        mail.send(msg)
    except Exception as e:
        # Log the error but don't crash the application
        current_app.logger.error(f"Failed to send email: {str(e)}")

@bp.route('/remove-my-interest/<int:property_id>')
@login_required
def remove_my_interest(property_id):
    if current_user.user_type != 'buyer':
        flash('Only buyers can remove their interest in properties', 'danger')
        return redirect(url_for('main.index'))
    
    property = Property.query.get_or_404(property_id)
    
    # Find the interest
    interest = PropertyInterest.query.filter_by(
        property_id=property_id,
        buyer_id=current_user.id
    ).first()
    
    if not interest:
        flash('You have not shown interest in this property', 'warning')
        return redirect(url_for('user.dashboard'))
    
    # Delete related chats and messages
    from app.models.chat import Chat, ChatMessage
    
    # Get chat related to this property and user
    chat = Chat.query.filter_by(
        property_id=property_id,
        buyer_id=current_user.id
    ).first()
    
    if chat:
        # Delete all messages in this chat
        ChatMessage.query.filter_by(chat_id=chat.id).delete()
        # Delete the chat
        db.session.delete(chat)
    
    # Delete the interest
    db.session.delete(interest)
    db.session.commit()
    
    flash('Your interest in this property has been removed', 'success')
    return redirect(url_for('user.dashboard'))

@bp.route('/image/<int:id>/delete')
@login_required
def delete_image(id):
    image = PropertyImage.query.get_or_404(id)
    property = Property.query.get_or_404(image.property_id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to delete this image', 'danger')
        return redirect(url_for('property.edit', id=property.id))
    
    was_primary = image.is_primary
    db.session.delete(image)
    
    # If the deleted image was primary, set a new primary image
    if was_primary and property.images:
        property.images[0].is_primary = True
    
    db.session.commit()
    flash('Image deleted successfully', 'success')
    return redirect(url_for('property.edit', id=property.id))

@bp.route('/image/<int:id>/set-primary')
@login_required
def set_primary_image(id):
    image = PropertyImage.query.get_or_404(id)
    property = Property.query.get_or_404(image.property_id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to modify this property', 'danger')
        return redirect(url_for('property.edit', id=property.id))
    
    # Reset all images to non-primary
    for img in property.images:
        img.is_primary = False
    
    # Set the selected image as primary
    image.is_primary = True
    db.session.commit()
    
    flash('Primary image updated successfully', 'success')
    return redirect(url_for('property.edit', id=property.id))

@bp.route('/property/<int:id>/add-document', methods=['POST'])
@login_required
def add_document(id):
    property = Property.query.get_or_404(id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to modify this property', 'danger')
        return redirect(url_for('property.edit', id=property.id))
    
    document_file = request.files.get('property_document')
    document_type = request.form.get('document_type')
    
    if document_file and document_file.filename and document_type:
        document_filename, document_url = save_property_document(document_file)
        if document_filename and document_url:
            property_document = PropertyDocument(
                property_id=property.id,
                filename=document_filename,
                url=document_url,
                document_type=document_type,
                is_verified=False
            )
            db.session.add(property_document)
            db.session.commit()
            flash('Document uploaded successfully', 'success')
    else:
        flash('Please select a document and document type', 'danger')
    
    return redirect(url_for('property.edit', id=property.id))

@bp.route('/document/<int:id>/delete')
@login_required
def delete_document(id):
    document = PropertyDocument.query.get_or_404(id)
    property = Property.query.get_or_404(document.property_id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to delete this document', 'danger')
        return redirect(url_for('property.edit', id=property.id))
    
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully', 'success')
    return redirect(url_for('property.edit', id=property.id))

@bp.route('/property/<int:id>/update-details', methods=['POST'])
@login_required
def update_details(id):
    property = Property.query.get_or_404(id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to modify this property', 'danger')
        return redirect(url_for('property.details', id=property.id))
    
    property.title = request.form.get('title')
    property.description = request.form.get('description')
    property.price = float(request.form.get('price'))
    property.property_type = request.form.get('property_type')
    property.location = request.form.get('location')
    property.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
    property.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
    property.area = float(request.form.get('area'))
    property.bedrooms = int(request.form.get('bedrooms')) if request.form.get('bedrooms') else None
    property.bathrooms = int(request.form.get('bathrooms')) if request.form.get('bathrooms') else None
    property.total_floors = int(request.form.get('total_floors')) if request.form.get('total_floors') else None
    
    db.session.commit()
    flash('Property details updated successfully!', 'success')
    return redirect(url_for('property.edit', id=property.id))

@bp.route('/property/<int:id>/add-images', methods=['POST'])
@login_required
def add_images(id):
    property = Property.query.get_or_404(id)
    
    # Check if current user is the owner
    if property.user_id != current_user.id:
        flash('You do not have permission to modify this property', 'danger')
        return redirect(url_for('property.details', id=property.id))
    
    # Handle multiple image uploads
    images = request.files.getlist('property_images')
    image_count = 0
    
    for image in images:
        if image and image.filename:
            image_filename, image_url = save_property_image(image)
            if image_filename and image_url:
                # Check if this is the first image for the property
                is_first = len(property.images) == 0
                property_image = PropertyImage(
                    property_id=property.id,
                    filename=image_filename,
                    url=image_url,
                    is_primary=is_first
                )
                db.session.add(property_image)
                image_count += 1
    
    if image_count > 0:
        db.session.commit()
        flash(f'{image_count} images uploaded successfully!', 'success')
    else:
        flash('No valid images were uploaded', 'warning')
        
    return redirect(url_for('property.edit', id=property.id)) 