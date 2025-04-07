from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import razorpay
from app.models.payment import Payment
from app.models.contract import Contract
from app.extensions import db
from datetime import datetime
import requests

bp = Blueprint('payment', __name__, url_prefix='/payment')

def get_razorpay_client():
    try:
        key_id = current_app.config.get('RAZORPAY_KEY_ID')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        if not key_id or not key_secret:
            current_app.logger.error("Razorpay credentials not configured")
            raise ValueError("Payment service not properly configured")
        
        # Create client with proper auth format and timeout settings
        client = razorpay.Client(
            auth=(key_id.strip(), key_secret.strip()),
            requests_kwargs={
                'timeout': 5,  # 5 seconds timeout
                'verify': True  # Verify SSL certificates
            }
        )
        
        # Test the client with a valid API call
        try:
            client.order.all()
            current_app.logger.info("Razorpay client initialized successfully")
            return client
        except requests.exceptions.ConnectionError as e:
            current_app.logger.error(f"Razorpay connection error: {str(e)}")
            raise ValueError("Unable to connect to payment service. Please check your internet connection.")
        except requests.exceptions.Timeout as e:
            current_app.logger.error(f"Razorpay timeout error: {str(e)}")
            raise ValueError("Payment service timeout. Please try again.")
        except Exception as e:
            current_app.logger.error(f"Razorpay API test failed: {str(e)}")
            raise ValueError("Failed to verify payment service")
            
    except Exception as e:
        current_app.logger.error(f"Razorpay client initialization error: {str(e)}")
        raise ValueError("Payment service configuration error")

@bp.route('/create-order/<int:contract_id>', methods=['POST'])
@login_required
def create_order(contract_id):
    try:
        contract = Contract.query.get_or_404(contract_id)
        if current_user.id != contract.buyer_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if contract.advance_payment_made:
            return jsonify({'error': 'Advance payment already made'}), 400
        
        client = get_razorpay_client()
        
        # Convert to a smaller amount for testing (1/100 of actual amount)
        test_amount = int(contract.advance_payment)  # Already in paise
        order_currency = 'INR'
        
        order_data = {
            'amount': test_amount,
            'currency': order_currency,
            'receipt': f'contract_{contract_id}',
            'payment_capture': 1,
            'notes': {
                'contract_id': str(contract_id),
                'actual_amount': str(contract.advance_payment)
            }
        }
        
        try:
            razorpay_order = client.order.create(order_data)
            current_app.logger.info(f"Razorpay order created: {razorpay_order['id']}")
            
            payment = Payment(
                contract_id=contract_id,
                amount=contract.advance_payment,
                razorpay_order_id=razorpay_order['id']
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'order_id': razorpay_order['id'],
                'amount': test_amount,
                'currency': order_currency,
                'key': current_app.config['RAZORPAY_KEY_ID'].strip()
            })
            
        except razorpay.errors.BadRequestError as e:
            current_app.logger.error(f"Razorpay order creation error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Invalid payment request. Please check the amount.'}), 400
        except Exception as e:
            current_app.logger.error(f"Razorpay order creation error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Payment service error'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Payment creation error: {str(e)}")
        return jsonify({'error': 'Payment initialization failed'}), 500

@bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json()
    
    client = get_razorpay_client()
    
    try:
        client.utility.verify_payment_signature(data)
        
        # Update payment status
        payment = Payment.query.filter_by(
            razorpay_order_id=data['razorpay_order_id']
        ).first()
        
        if payment:
            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.status = 'completed'
            
            # Update contract status
            contract = payment.contract
            contract.advance_payment_made = True
            contract.status = 'active'
            
            # Update property status to sold
            property = contract.property
            property.is_available = False
            property.status = 'sold'
            
            db.session.commit()
            return jsonify({'status': 'success'})
            
    except Exception as e:
        current_app.logger.error(f"Payment verification error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/create-full-payment/<int:contract_id>', methods=['POST'])
@login_required
def create_full_payment(contract_id):
    try:
        contract = Contract.query.get_or_404(contract_id)
        
        if current_user.id != contract.buyer_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        if contract.full_payment_made:
            return jsonify({'error': 'Payment already made'}), 400
            
        if contract.payment_deadline < datetime.utcnow():
            return jsonify({'error': 'Payment deadline has passed'}), 400
        
        client = get_razorpay_client()
        
        # Calculate remaining amount and convert to test amount
        remaining_amount = contract.price - contract.advance_payment
        test_amount = int(remaining_amount)  # Already in paise, smaller test amount
        
        order_data = {
            'amount': test_amount,
            'currency': 'INR',
            'receipt': f'contract_full_{contract_id}',
            'payment_capture': 1,
            'notes': {
                'contract_id': str(contract_id),
                'actual_amount': str(remaining_amount)
            }
        }
        
        try:
            razorpay_order = client.order.create(order_data)
            
            payment = Payment(
                contract_id=contract_id,
                amount=remaining_amount,
                razorpay_order_id=razorpay_order['id']
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'order_id': razorpay_order['id'],
                'amount': test_amount,
                'currency': 'INR',
                'key': current_app.config['RAZORPAY_KEY_ID'].strip()
            })
            
        except Exception as e:
            current_app.logger.error(f"Razorpay full payment order creation error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Payment service error'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Payment initialization failed'}), 500

@bp.route('/verify-full-payment', methods=['POST'])
@login_required
def verify_full_payment():
    data = request.get_json()
    
    client = get_razorpay_client()
    
    try:
        client.utility.verify_payment_signature(data)
        
        # Update payment status
        payment = Payment.query.filter_by(
            razorpay_order_id=data['razorpay_order_id']
        ).first()
        
        if payment:
            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.status = 'completed'
            
            # Update contract status
            contract = payment.contract
            contract.full_payment_made = True
            contract.full_payment_date = datetime.utcnow()
            contract.status = 'completed'
            
            db.session.commit()
            return jsonify({'status': 'success'})
            
    except Exception as e:
        current_app.logger.error(f"Full payment verification error: {str(e)}")
        return jsonify({'error': str(e)}), 400 