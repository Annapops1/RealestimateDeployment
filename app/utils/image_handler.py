import os
import secrets
from PIL import Image
from flask import current_app

def save_property_image(image_file, folder='property_images'):
    """Save a property image and return filename and URL"""
    if not image_file or not image_file.filename:
        return None, None
        
    # Generate random filename
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(image_file.filename)
    filename = random_hex + file_ext
    
    # Create path and save
    upload_folder = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    
    # Resize and save image
    output_size = (1200, 800)
    img = Image.open(image_file)
    img.thumbnail(output_size)
    img.save(filepath)
    
    # Return filename and URL
    image_url = f'/static/{folder}/{filename}'
    return filename, image_url 