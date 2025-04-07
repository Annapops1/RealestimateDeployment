from app import db
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from app.models.chat import Chat

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    property_type = db.Column(db.String(50))  # 'house', 'apartment', 'plot'
    
    # Location details
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Common fields
    area = db.Column(db.Float)  # in square feet
    area_unit = db.Column(db.String(20), default='sq_ft')
    
    # Building-specific fields (for houses and apartments)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    floor = db.Column(db.Integer)  # for apartments
    total_floors = db.Column(db.Integer)
    
    # Plot-specific fields
    plot_dimensions = db.Column(db.String(50))  # e.g., "40x60"
    corner_plot = db.Column(db.Boolean, default=False)
    facing = db.Column(db.String(20))  # North, South, East, West
    
    # Add image fields
    image_filename = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    # Verification fields
    is_verified = db.Column(db.Boolean, default=False)
    verification_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_feedback = db.Column(db.Text)  # For rejection reason
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Define the relationship without backref
    interests = db.relationship('PropertyInterest', lazy='dynamic', cascade='all, delete-orphan')

    # Add this to the existing Property model
    images = db.relationship('PropertyImage', back_populates='property', cascade='all, delete-orphan')
    documents = db.relationship('PropertyDocument', back_populates='property', cascade='all, delete-orphan')

    @property
    def has_interests(self):
        """Check if property has any interests"""
        return self.interests.count() > 0

    def has_user_interest(self, user_id):
        """Check if a specific user has shown interest in this property"""
        from app.models.interest import PropertyInterest
        return PropertyInterest.query.filter_by(
            property_id=self.id,
            buyer_id=user_id
        ).first() is not None

    def get_chat_with_user(self, user_id):
        """Get existing chat between property owner and user"""
        return Chat.query.filter(
            Chat.property_id == self.id,
            ((Chat.buyer_id == user_id) & (Chat.seller_id == self.user_id)) |
            ((Chat.seller_id == user_id) & (Chat.buyer_id == self.user_id))
        ).first()

    def distance_to(self, lat2, lon2):
        """Calculate distance between property and given coordinates in km"""
        # Check if any coordinates are None
        if self.latitude is None or self.longitude is None or lat2 is None or lon2 is None:
            return float('inf')  # Return infinity if coordinates are missing
        
        # Convert decimal degrees to radians
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(lat2), radians(lon2)
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Radius of earth in kilometers
        r = 6371
        
        # Calculate distance
        return c * r 

    def get_active_contract(self):
        """Return the active contract for this property if it exists"""
        from app.models.contract import Contract
        return Contract.query.filter(
            Contract.property_id == self.id,
            Contract.status.in_(['pending', 'active', 'approved'])
        ).first()
    
    def has_active_contract(self):
        """Check if property has any active contracts"""
        return self.get_active_contract() is not None
    
    def has_interests(self):
        """Check if property has any buyer interests"""
        from app.models.interest import PropertyInterest
        return PropertyInterest.query.filter_by(property_id=self.id).count() > 0

    # Add a helper method to get the primary image
    def get_primary_image(self):
        """Get the primary image for this property"""
        primary = next((img for img in self.images if img.is_primary), None)
        if primary:
            return primary
        # If no primary image is set, return the first image or None
        return self.images[0] if self.images else None 