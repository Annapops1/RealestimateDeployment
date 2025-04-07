from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.chatbot import get_buyer_response, get_seller_response, extract_page_content

bp = Blueprint('ai_chat', __name__, url_prefix='/ai-chat')

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
        print(f"Error in AI chat route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500 