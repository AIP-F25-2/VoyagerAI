from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# IMPORTANT: use the single SQLAlchemy instance from models (sujan branch)
from .models import db  # noqa: E402


def create_app():
    app = Flask(__name__)

    # Enable CORS for frontend (allow 3000 and 3001) and general CORS
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}})

    # Database configuration for SQLAlchemy (sujan)
    database_url = os.getenv("DATABASE_URL", "sqlite:///voyagerai.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy
    db.init_app(app)

    # Ensure models are registered
    from . import models  # noqa: F401

    # Register blueprints
    from .routes import bp as api_bp
    from .auth import auth_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    @app.route("/")
    def index():
        return {
            "message": "VoyagerAI Backend Running",
            "routes": ["/api/", "/api/events", "/api/events/fetch"],
        }

    return app
