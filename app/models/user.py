from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager
from app.models.property import Property
from app.utils.recommendation_engine import recommendation_engine

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    # Override UserMixin's is_active with our own column
    active = db.Column(db.Boolean, default=True)
    
    # Additional profile fields
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    
    # Property preferences
    preferred_property_type = db.Column(db.String(50))
    preferred_location = db.Column(db.String(100))
    min_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    min_bedrooms = db.Column(db.Integer)
    
    # Google Maps integration
    preferred_latitude = db.Column(db.Float)
    preferred_longitude = db.Column(db.Float)
    
    # User type
    user_type = db.Column(db.String(20), nullable=False, default='buyer')  # 'buyer' or 'seller'
    company_name = db.Column(db.String(100))  # For sellers/agents
    license_number = db.Column(db.String(50))  # For sellers/agents
    verified_seller = db.Column(db.Boolean, default=False)
    
    # New field
    preferred_proximity = db.Column(db.Float, default=10.0)  # Default 10km radius
    
    properties = db.relationship(
        'Property',
        backref='owner',
        lazy=True,
        foreign_keys='Property.user_id'
    )
    
    verified_properties = db.relationship(
        'Property',
        backref='verified_by_admin',
        lazy=True,
        foreign_keys='Property.verified_by'
    )
    
    wishlisted_properties = db.relationship('Property', 
                                          secondary='wishlist',
                                          backref=db.backref('wishlisted_by', lazy='dynamic'))

    # Override UserMixin's is_active property
    @property
    def is_active(self):
        return self.active
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_profile_complete(self):
        if self.is_admin:
            return True
        if self.user_type == 'buyer':
            return bool(
                self.phone_number and 
                self.address and 
                self.city and 
                self.state
            )
        # For sellers, always return true to allow navigation
        if self.user_type == 'seller':
            return True
        # For users who haven't selected a type yet
        return False

    def get_recommended_properties(self, limit=5):
        """
        Get recommended properties using the hybrid recommendation engine
        """
        # If user has no preferences yet, fall back to location-based recommendations
        if not self.preferred_latitude or not self.preferred_longitude:
            # Use existing location-based method
            max_distance = self.preferred_proximity or 10.0
            
            query = Property.query.filter(
                Property.is_available == True,
                Property.is_verified == True,
                Property.verification_status == 'approved',
                Property.user_id != self.id
            )
            
            if self.preferred_property_type:
                query = query.filter(Property.property_type == self.preferred_property_type)
            
            if self.min_price:
                query = query.filter(Property.price >= self.min_price)
            if self.max_price:
                query = query.filter(Property.price <= self.max_price)
            
            properties = query.all()
            recommended = []
            
            for prop in properties:
                if not prop.latitude or not prop.longitude:
                    continue
                
                distance = prop.distance_to(self.preferred_latitude, self.preferred_longitude)
                if distance <= max_distance:
                    score = 1 - (distance / max_distance)
                    recommended.append((prop, score))
            
            recommended.sort(key=lambda x: x[1], reverse=True)
            return [prop for prop, _ in recommended[:limit]]
        
        # Use the hybrid recommendation engine
        return recommendation_engine.get_hybrid_recommendations(self.id, limit=limit)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 