from flask import Blueprint, request, jsonify
from functools import wraps
from .models import db, User
from .services.email_service import email_service
from datetime import datetime
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
        
        # Generate verification token
        verification_token = user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        email_sent = email_service.send_verification_email(
            user_email=user.email,
            user_name=user.name,
            verification_token=verification_token
        )
        
        # Generate auth token
        token = user.generate_token()
        
        return jsonify({
            "success": True,
            "message": "User created successfully. Please check your email to verify your account.",
            "token": token,
            "user": user.to_dict(),
            "email_sent": email_sent
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

@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    """Verify user email with token"""
    try:
        data = request.get_json()
        token = data.get("token", "")
        
        if not token:
            return jsonify({"success": False, "message": "Verification token is required"}), 400
        
        user = User.verify_token(token, 'email_verification')
        if not user:
            return jsonify({"success": False, "message": "Invalid or expired verification token"}), 400
        
        if user.is_verified:
            return jsonify({"success": True, "message": "Email already verified"}), 200
        
        # Mark user as verified
        user.is_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Email verified successfully",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error verifying email: {str(e)}"}), 500

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Resend email verification"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        if user.is_verified:
            return jsonify({"success": False, "message": "Email already verified"}), 400
        
        # Generate new verification token
        verification_token = user.generate_verification_token()
        db.session.commit()
        
        # Send verification email
        email_sent = email_service.send_verification_email(
            user_email=user.email,
            user_name=user.name,
            verification_token=verification_token
        )
        
        return jsonify({
            "success": True,
            "message": "Verification email sent",
            "email_sent": email_sent
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error resending verification: {str(e)}"}), 500

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if user exists or not for security
            return jsonify({
                "success": True,
                "message": "If an account with that email exists, a password reset link has been sent"
            }), 200
        
        # Generate password reset token
        reset_token = user.generate_password_reset_token()
        db.session.commit()
        
        # Send password reset email
        email_sent = email_service.send_password_reset_email(
            user_email=user.email,
            user_name=user.name,
            reset_token=reset_token
        )
        
        return jsonify({
            "success": True,
            "message": "If an account with that email exists, a password reset link has been sent",
            "email_sent": email_sent
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error sending password reset: {str(e)}"}), 500

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        token = data.get("token", "")
        new_password = data.get("password", "")
        
        if not token:
            return jsonify({"success": False, "message": "Reset token is required"}), 400
        
        if not new_password:
            return jsonify({"success": False, "message": "New password is required"}), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"success": False, "message": message}), 400
        
        user = User.verify_token(token, 'password_reset')
        if not user:
            return jsonify({"success": False, "message": "Invalid or expired reset token"}), 400
        
        # Check if reset token is still valid
        if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
            return jsonify({"success": False, "message": "Reset token has expired"}), 400
        
        # Update password and clear reset token
        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Password reset successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error resetting password: {str(e)}"}), 500
