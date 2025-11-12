"""
Centralized error handling for the VoyagerAI backend
"""
from flask import jsonify
import logging
import os
from functools import wraps

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


# Helper functions to reduce code duplication
def success_response(data=None, message=None, status_code=200):
    """Create a standardized success response"""
    response = {"success": True}
    if message:
        response["message"] = message
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response["data"] = data
    return jsonify(response), status_code


def error_response(error_message, status_code=400, error_code=None):
    """Create a standardized error response"""
    response = {"success": False, "error": error_message}
    if error_code:
        response["error_code"] = error_code
    return jsonify(response), status_code


def handle_route_exception(func):
    """Decorator to handle exceptions in route handlers and reduce duplication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            return error_response(e.message, e.status_code, e.error_code)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            is_production = os.getenv('FLASK_ENV') == 'production'
            error_msg = "An internal error occurred. Please try again later." if is_production else str(e)
            return error_response(error_msg, 500)
    return wrapper

