"""
Centralized error handling for the VoyagerAI backend
"""
from flask import jsonify
import logging
import os

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API exception"""
    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

def handle_error(error):
    """Global error handler for Flask app"""
    if isinstance(error, APIError):
        response = {
            "success": False,
            "error": error.message,
            "error_code": error.error_code
        }
        logger.warning(f"API Error: {error.message} (code: {error.error_code})")
        return jsonify(response), error.status_code
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    # Don't expose internal errors in production
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    response = {
        "success": False,
        "error": "An internal error occurred. Please try again later." if is_production else str(error)
    }
    
    return jsonify(response), 500

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    app.register_error_handler(APIError, handle_error)
    app.register_error_handler(Exception, handle_error)

