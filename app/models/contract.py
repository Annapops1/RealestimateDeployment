from app.extensions import db
from datetime import datetime

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Contract details
    price = db.Column(db.Float, nullable=False)
    advance_payment = db.Column(db.Float, nullable=False)
    payment_deadline = db.Column(db.DateTime, nullable=False)
    terms = db.Column(db.Text, nullable=False)
    
    # Status tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    seller_accepted = db.Column(db.Boolean, default=False)
    buyer_accepted = db.Column(db.Boolean, default=False)
    advance_payment_made = db.Column(db.Boolean, default=False)
    full_payment_made = db.Column(db.Boolean, default=False)
    full_payment_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, cancelled
    
    # Relationships
    property = db.relationship('Property', backref='contracts')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='seller_contracts')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='buyer_contracts') 