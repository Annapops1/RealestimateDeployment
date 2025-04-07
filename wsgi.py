import os
from app import create_app

# Set environment variables
os.environ['FLASK_APP'] = 'wsgi.py'
os.environ['FLASK_ENV'] = 'production'

# Create the application
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000))) 