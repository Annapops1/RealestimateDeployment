from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.contract import Contract
from app.models.property import Property
from app.extensions import db
from datetime import datetime, timedelta

bp = Blueprint('contract', __name__, url_prefix='/contract')

@bp.route('/create/<int:property_id>/<int:buyer_id>', methods=['GET', 'POST'])
@login_required
def create(property_id, buyer_id):
    if current_user.user_type != 'seller':
        flash('Only sellers can create contracts', 'danger')
        return redirect(url_for('main.index'))
    
    property = Property.query.get_or_404(property_id)
    if property.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('main.index'))
    
    # Prevent contract creation for unapproved properties
    if not property.is_verified or property.verification_status != 'approved':
        flash('This property is not available for purchase', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        payment_deadline = datetime.strptime(request.form.get('payment_deadline'), '%Y-%m-%d')
        min_deadline = datetime.now() + timedelta(days=15)
        
        if payment_deadline.date() < min_deadline.date():
            flash('Payment deadline must be at least 15 days from today', 'danger')
            return render_template('contract/create.html', property=property)
            
        contract = Contract(
            property_id=property_id,
            seller_id=current_user.id,
            buyer_id=buyer_id,
            price=float(request.form.get('price')),
            advance_payment=float(request.form.get('advance_payment')),
            payment_deadline=payment_deadline,
            terms=request.form.get('terms'),
            seller_accepted=True
        )
        
        db.session.add(contract)
        db.session.commit()
        
        flash('Contract created successfully', 'success')
        return redirect(url_for('contract.details', contract_id=contract.id))
    
    now = datetime.now()
    return render_template('contract/create.html', 
                         property=property,
                         now=now,
                         timedelta=timedelta)

@bp.route('/<int:contract_id>/accept')
@login_required
def accept(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    property = Property.query.get(contract.property_id)
    
    if current_user.id != contract.buyer_id:
        flash('Only the buyer can accept this contract', 'danger')
        return redirect(url_for('contract.details', contract_id=contract_id))
    
    contract.buyer_accepted = True
    if contract.seller_accepted and contract.buyer_accepted:
        contract.status = 'active'
        # Mark property as unavailable
        property.is_available = False
        
    db.session.commit()
    flash('Contract accepted successfully', 'success')
    return redirect(url_for('contract.details', contract_id=contract_id))

@bp.route('/details/<int:contract_id>')
@login_required
def details(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    
    # Check if user is either buyer or seller
    if current_user.id not in [contract.buyer_id, contract.seller_id]:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('contract/details.html', contract=contract) 