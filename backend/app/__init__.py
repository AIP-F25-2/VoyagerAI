from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from sentry_sdk.integrations.flask import FlaskIntegration
import sentry_sdk
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# IMPORTANT: use the single SQLAlchemy instance from models (sujan branch)
from .models import db  # noqa: E402

# Extensions (singletons)
limiter = Limiter(get_remote_address, storage_uri="memory://")
cache = Cache()


def create_app():
    # Security Hotspot Review: CSRF protection is not enabled because this is a REST API using
    # JWT token-based authentication (not cookie-based sessions). JWT tokens are sent in
    # Authorization headers, which are not vulnerable to CSRF attacks. CORS is properly configured
    # to restrict origins. This security hotspot has been reviewed and determined to be safe for
    # this use case. See: https://owasp.org/www-community/attacks/csrf
    app = Flask(__name__)

    # Validate required environment variables
    required_vars = ['JWT_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set these in your .env file. See env.example for reference."
        )

    # Sentry (optional)
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()])

    # CORS: env-based allowed origins
    # Security Hotspot Review: HTTP is used in the default value for localhost development only.
    # In production, FRONTEND_ORIGINS should be set via environment variable with HTTPS URLs.
    # Localhost HTTP is safe for local development and is not a security risk.
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

    # Register error handlers
    from .utils.error_handler import register_error_handlers
    register_error_handlers(app)

    # Initialize Elasticsearch (optional, won't fail if unavailable)
    with app.app_context():
        try:
            from .services.elasticsearch_service import es_service
            if es_service.is_available():
                es_service.create_index()
                print("✅ Elasticsearch initialized and index created")
            else:
                print("⚠️  Elasticsearch not available, using fallback search")
        except Exception as e:
            print(f"⚠️  Elasticsearch initialization failed: {e}")
            print("   Events will still work with fallback search")

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
            
            # Check Elasticsearch status
            es_status = {"available": False}
            try:
                from .services.elasticsearch_service import es_service
                es_status = es_service.get_index_stats()
            except Exception:
                pass
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": "connected",
                "event_count": event_count,
                "elasticsearch": es_status,
                "version": "1.0.0"
            }, 200
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }, 500

    return app
