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
    GOOGLE_MAPS_API_KEY = 'AIzaSyCSBc2kMpkFNkrOk3dwPYJiYbmq4MnKOt0' 
    
    # Separate upload folders for properties and chat files
    PROPERTY_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads/properties')
    CHAT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads/chat_files')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 
    GOOGLE_GEMINI_API_KEY = 'AIzaSyAGJY8OIgX5r0h7rVXa30qUmmMFsRA8lr0'
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID = 'rzp_test_1vZK3GexmGW5zt'
    RAZORPAY_KEY_SECRET = 'eIKYygydEQ5iicHT2N6gaVuC'
    
    GOOGLE_OAUTH_CLIENT_ID = '618443740802-cfcdj8nvd35sg0om1s1m1a2k9gb2ve28.apps.googleusercontent.com'
    GOOGLE_OAUTH_CLIENT_SECRET = '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'
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'  # Or your preferred mail server
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'realestimateindia@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'pkut mqit aguu ykjj'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'realestimateindia@gmail.com'