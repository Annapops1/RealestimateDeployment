from app import db
from datetime import datetime

class PropertyDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)  # tax, deed, title, other
    is_verified = db.Column(db.Boolean, default=False)
    admin_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Define relationship with Property
    property = db.relationship('Property', back_populates='documents') 