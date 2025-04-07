from datetime import datetime
from app.extensions import db

class PropertyInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Define relationship without backref
    property = db.relationship('Property', foreign_keys=[property_id])
    buyer = db.relationship('User', backref='property_interests')
    
    __table_args__ = (db.UniqueConstraint('property_id', 'buyer_id', name='unique_property_buyer'),)