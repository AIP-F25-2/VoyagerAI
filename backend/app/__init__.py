from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from .routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return {
            "message": "VoyagerAI Backend Running",
            "routes": ["/api/", "/api/events?q=Toronto"]
        }

    return app
