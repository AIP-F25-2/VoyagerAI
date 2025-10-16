from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# IMPORTANT: use the single SQLAlchemy instance from models (sujan branch)
from .models import db  # noqa: E402

# Extensions (singletons)
limiter = Limiter(get_remote_address, storage_uri="memory://")
cache = Cache()


def create_app():
    app = Flask(__name__)

    # Sentry (optional)
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()])

    # CORS: env-based allowed origins
    origins_env = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:3001")
    allowed_origins = [o.strip() for o in origins_env.split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    # Database configuration for SQLAlchemy (sujan)
    database_url = os.getenv("DATABASE_URL", "sqlite:///voyagerai.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize extensions
    limiter.init_app(app)
    cache.init_app(app, config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 60,
    })

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

    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            from .models import Event
            event_count = Event.query.count()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected",
                "event_count": event_count,
                "version": "1.0.0"
            }, 200
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }, 500

    return app
