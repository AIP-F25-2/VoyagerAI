from flask import Blueprint, request, jsonify
from functools import wraps
from .models import db, User
import re

auth_bp = Blueprint("auth", __name__)

def token_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        user = User.verify_token(token)
        if not user:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Valid password"

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validation
        if not name:
            return jsonify({"success": False, "message": "Name is required"}), 400
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        if not validate_email(email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        if not password:
            return jsonify({"success": False, "message": "Password is required"}), 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"success": False, "message": message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"success": False, "message": "User with this email already exists"}), 400
        
        # Create new user
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = user.generate_token()
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "token": token,
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error creating user: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validation
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        if not password:
            return jsonify({"success": False, "message": "Password is required"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({"success": False, "message": "Invalid email or password"}), 401
        
        if not user.is_active:
            return jsonify({"success": False, "message": "Account is deactivated"}), 401
        
        # Generate token
        token = user.generate_token()
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error during login: {str(e)}"}), 500

@auth_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(user):
    """Get current user profile"""
    return jsonify({
        "success": True,
        "user": user.to_dict()
    }), 200

@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile(user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Update name if provided
        if "name" in data:
            name = data["name"].strip()
            if name:
                user.name = name
        
        # Update email if provided
        if "email" in data:
            email = data["email"].strip().lower()
            if email and validate_email(email):
                # Check if email is already taken by another user
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({"success": False, "message": "Email already in use"}), 400
                user.email = email
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error updating profile: {str(e)}"}), 500

@auth_bp.route("/change-password", methods=["POST"])
@token_required
def change_password(user):
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        
        # Validation
        if not current_password:
            return jsonify({"success": False, "message": "Current password is required"}), 400
        
        if not new_password:
            return jsonify({"success": False, "message": "New password is required"}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({"success": False, "message": "Current password is incorrect"}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"success": False, "message": message}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error changing password: {str(e)}"}), 500

@auth_bp.route("/verify-token", methods=["POST"])
def verify_token():
    """Verify if a token is valid"""
    try:
        data = request.get_json()
        token = data.get("token", "")
        
        if not token:
            return jsonify({"success": False, "message": "Token is required"}), 400
        
        user = User.verify_token(token)
        if not user:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 401
        
        return jsonify({
            "success": True,
            "message": "Token is valid",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error verifying token: {str(e)}"}), 500
