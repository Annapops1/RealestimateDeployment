import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'realestimate.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key-here'  # Change this to a secure secret key 
    GOOGLE_MAPS_API_KEY = 'AIzaSyAR5UzoEbsm9hdEdoEP_aHzpBxsVz-ROqI' 
    
    # Separate upload folders for properties and chat files
    PROPERTY_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads/properties')
    CHAT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads/chat_files')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 
    GOOGLE_GEMINI_API_KEY = 'AIzaSyAGJY8OIgX5r0h7rVXa30qUmmMFsRA8lr0' 
    RAZORPAY_KEY_ID = 'rzp_test_0NbQGdFY24Qd5G'
    RAZORPAY_KEY_SECRET = 'Z1msuCYPvMKWLt8njWSpKpQK'