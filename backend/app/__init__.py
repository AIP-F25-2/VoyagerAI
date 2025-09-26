from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# IMPORTANT: use the single SQLAlchemy instance from models
from .models import db  # noqa: E402

def create_app():
    app = Flask(__name__)
    
    # Enable CORS for frontend (allow 3000 and 3001)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}})
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///voyagerai.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Import models to register them
    from . import models
    
    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp, url_prefix='/api')
    
    return app