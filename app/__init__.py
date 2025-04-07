from flask import Flask
from flask_migrate import Migrate
from config import Config
from app.extensions import db, login_manager
import os
from app.cli import create_admin
from flask_wtf.csrf import CSRFProtect
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_login import current_user
from app.models.oauth import OAuth
import threading
from flask_mail import Mail

# Allow OAuth over HTTP for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

csrf = CSRFProtect()
migrate = Migrate()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Register Google OAuth blueprint
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_to='user.google_authorized',
        offline=True,
        reprompt_consent=True
    )
    
    from app.routes import auth, user, admin, main, property, chat, payment, contract
    app.register_blueprint(auth.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(property.bp, url_prefix='/property')
    app.register_blueprint(chat.bp, url_prefix='/chat')
    app.register_blueprint(payment.bp)
    app.register_blueprint(contract.bp)

    app.register_blueprint(google_bp, url_prefix='/google_login')
    # Set up login manager
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Start recommendation engine update thread
    with app.app_context():
        def start_recommendation_thread():
            from app.tasks import update_recommendation_engine
            recommendation_thread = threading.Thread(target=update_recommendation_engine)
            recommendation_thread.daemon = True
            recommendation_thread.start()
        
        # Use Flask 2.x compatible approach
        app.before_request_funcs.setdefault(None, []).append(start_recommendation_thread)
    
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None:
            return "0"
        return "{:,.2f}".format(value)
    
    return app