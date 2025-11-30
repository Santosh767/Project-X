from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User

def role_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'error': 'Account is inactive'}), 403
            
            if user.role not in allowed_roles:
                return jsonify({'error': 'Access denied'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user():
    """Get current logged-in user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)