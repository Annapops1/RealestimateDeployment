from flask import Blueprint, jsonify, request, render_template, current_app, url_for, send_from_directory, abort
from flask_login import login_required, current_user
from app.utils.chatbot import get_buyer_response, get_seller_response, extract_page_content
from app.models.chat import Chat, ChatMessage
from app.models.property import Property
from app.models.contract import Contract
from app.models.interest import PropertyInterest
from app.models.user import User
from app.extensions import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('chat', __name__, url_prefix='/chat')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/ask', methods=['POST'])
@login_required
def ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        query = data.get('query')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
            
        page_content = data.get('pageContent', '')
        
        if page_content:
            try:
                page_content = extract_page_content(page_content)
            except Exception as e:
                print(f"Error cleaning page content: {str(e)}")

        if current_user.user_type == 'buyer':
            preferences = {
                'type': current_user.preferred_property_type,
                'location': current_user.preferred_location,
                'budget': f"{current_user.min_price}-{current_user.max_price}",
                'bedrooms': current_user.min_bedrooms
            }
            response = get_buyer_response(query, preferences, page_content)
        else:
            response = get_seller_response(query, None, page_content)
            
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 

@bp.route('/property/<int:property_id>/chat/<int:other_user_id>')
@login_required
def property_chat(property_id, other_user_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if a chat already exists with these participants
    chat = Chat.query.filter(
        Chat.property_id == property_id,
        ((Chat.buyer_id == current_user.id) & (Chat.seller_id == other_user_id)) |
        ((Chat.seller_id == current_user.id) & (Chat.buyer_id == other_user_id))
    ).first()
    
    if not chat:
        chat = Chat(
            property_id=property_id,
            buyer_id=other_user_id if current_user.user_type == 'seller' else current_user.id,
            seller_id=current_user.id if current_user.user_type == 'seller' else other_user_id
        )
        db.session.add(chat)
        db.session.commit()
    
    # Get messages for this chat
    messages = ChatMessage.query.filter_by(chat_id=chat.id).order_by(ChatMessage.created_at).all()
    
    # Get associated contract if it exists
    contract = Contract.query.filter_by(
        property_id=property_id,
        buyer_id=chat.buyer_id,
        seller_id=chat.seller_id
    ).first()
    
    return render_template('chat/property_chat.html', 
                         chat=chat, 
                         messages=messages, 
                         contract=contract,
                         hide_ai_chat=True)

@bp.route('/my-chats')
@login_required
def my_chats():
    if current_user.user_type == 'buyer':
        # Get all properties where buyer has shown interest
        interests = PropertyInterest.query.filter_by(buyer_id=current_user.id)\
            .order_by(PropertyInterest.created_at.desc()).all()
            
        # Get all chats for these properties
        property_ids = [interest.property_id for interest in interests]
        chats = Chat.query.filter(
            Chat.property_id.in_(property_ids),
            Chat.buyer_id == current_user.id
        ).all()
        
        # Create a dictionary of property_id to chat
        chat_dict = {chat.property_id: chat for chat in chats}
        
        # Create a list of chat data including properties without chats
        chat_data = []
        for interest in interests:
            # Get the seller (user) through property's user_id
            seller = User.query.get(interest.property.user_id)
            chat_data.append({
                'property': interest.property,
                'seller': seller,
                'chat': chat_dict.get(interest.property_id),
                'last_message_at': chat_dict.get(interest.property_id).last_message_at if chat_dict.get(interest.property_id) else interest.created_at,
                'interest_date': interest.created_at
            })
            
        return render_template('chat/my_chats.html', chat_data=chat_data)
    else:
        # Existing seller logic
        chats = Chat.query.filter_by(seller_id=current_user.id)\
            .order_by(Chat.last_message_at.desc()).all()
        return render_template('chat/my_chats.html', chats=chats)

@bp.route('/send-message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    message = ChatMessage(
        chat_id=data['chat_id'],
        sender_id=current_user.id,
        content=data['content']
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'file_url': message.file_url if hasattr(message, 'file_url') else None,
        'file_name': message.file_name if hasattr(message, 'file_name') else None,
        'file_type': message.file_type if hasattr(message, 'file_type') else None,
        'created_at': message.created_at.isoformat(),
        'sender_id': message.sender_id
    })

@bp.route('/messages/<int:chat_id>')
@login_required
def get_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.buyer_id != current_user.id and chat.seller_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    messages = ChatMessage.query.filter_by(chat_id=chat_id)\
        .order_by(ChatMessage.created_at).all()
    
    # Mark unread messages as read
    unread_messages = ChatMessage.query.filter_by(
        chat_id=chat_id,
        is_read=False
    ).filter(ChatMessage.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    return jsonify({
        'messages': [{
            'content': message.content,
            'sender_id': message.sender_id,
            'timestamp': message.created_at.isoformat(),
            'is_sender': message.sender_id == current_user.id,
            'file_url': url_for('chat.download_file', filename=message.file_url) if message.file_url else None,
            'file_name': message.file_name,
            'file_type': message.file_type
        } for message in messages]
    })

@bp.route('/send-file', methods=['POST'])
@login_required
def send_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    chat_id = request.form.get('chat_id')
    
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
        
    if file.content_length and file.content_length > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large'}), 400
        
    # Generate a unique filename to prevent overwrites
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    unique_filename = timestamp + filename
    
    # Save file in the uploads directory
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat_files')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    message = ChatMessage(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=f'Sent file: {filename}',
        file_url=unique_filename,  # Store just the filename
        file_name=filename,  # Store original filename
        file_type=file.content_type
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'file_url': url_for('chat.download_file', filename=unique_filename),
        'file_name': filename,
        'file_type': message.file_type,
        'is_sender': True,
        'timestamp': message.created_at.isoformat()
    })

@bp.route('/download/<filename>')
@login_required
def download_file(filename):
    try:
        # Construct the absolute path to the uploads directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat_files')
        print(f"Looking for file: {filename} in directory: {upload_dir}")  # Debug log
        
        if not os.path.exists(os.path.join(upload_dir, filename)):
            print(f"File not found: {os.path.join(upload_dir, filename)}")  # Debug log
            abort(404)
            
        return send_from_directory(
            upload_dir,
            filename,
            as_attachment=True
        )
    except Exception as e:
        print(f"Error downloading file: {str(e)}")  # Debug log
        abort(404)