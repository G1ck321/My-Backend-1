# backend/stylus_api/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import Config
from .routes.wardrobe import wardrobe_bp
from .routes.events import events_bp
from .routes.profile import profile_bp
from .utils.auth import get_current_user_id
from .routes.chat import chat_bp
from .routes.context import context_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for both production and local development
    CORS(app, 
         resources={r"/api/*": {"origins": ["https://stylus-host.vercel.app","http://localhost:3000"]}}, 
         supports_credentials=True)
    
    # Register blueprints with clean prefixes
    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(wardrobe_bp, url_prefix="/api/wardrobe")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(chat_bp, url_prefix="/api") # Routes inside will be /api/chat-message
    app.register_blueprint(context_bp, url_prefix="/api") # Routes inside will be /api/weather, etc.
    
    return app