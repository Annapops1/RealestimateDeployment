import os
import secrets
from flask import current_app

def save_property_document(document_file, folder='property_documents'):
    """Save a property document and return filename and URL"""
    if not document_file or not document_file.filename:
        return None, None
        
    # Generate random filename
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(document_file.filename)
    filename = random_hex + file_ext
    
    # Create path and save
    upload_folder = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    
    # Save the document
    document_file.save(filepath)
    
    # Return filename and URL
    document_url = f'/static/{folder}/{filename}'
    return filename, document_url 