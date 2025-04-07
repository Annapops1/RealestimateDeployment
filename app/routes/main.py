from flask import Blueprint, render_template
from app.models.property import Property
from flask_login import current_user
from flask import current_app
from app.models.contract import Contract
from app.extensions import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get properties that are available, verified, and don't have contracts
    properties = Property.query.filter(
        Property.is_available == True,
        Property.is_verified == True,
        Property.verification_status == 'approved',
        ~Property.id.in_(
            db.session.query(Contract.property_id).filter(
                Contract.status.in_(['pending', 'active', 'approved'])
            )
        )
    ).order_by(Property.created_at.desc()).limit(6).all()
    
    recommended_properties = []
    
    if current_user.is_authenticated and current_user.user_type == 'buyer':
        recommended_properties = current_user.get_recommended_properties(limit=3)
    
    return render_template('index.html', 
                         properties=properties,
                         recommended_properties=recommended_properties,
                         google_maps_api_key=current_app.config['GOOGLE_MAPS_API_KEY']) 