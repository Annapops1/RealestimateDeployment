import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Set environment variables
os.environ['FLASK_APP'] = 'wsgi.py'
os.environ['FLASK_ENV'] = 'production'

# Create the application
application = create_app()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000))) 