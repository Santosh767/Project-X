from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt  # ← ADD bcrypt HERE
from app.models import User, Department
from app.utils.validators import validate_email, validate_phone, validate_password

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    """
    Patient registration endpoint
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name', 'phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if username exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if email exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new patient user
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            full_name=data['full_name'],
            phone=data['phone'],
            role='patient',
            gender=data.get('gender'),
            address=data.get('address'),
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'full_name': new_user.full_name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - CRITICAL for Vue frontend
    Expected format from frontend: { "username": "...", "password": "..." }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 401
        
        # Verify password
        if not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        # ✅ CRITICAL: Return format that Vue frontend expects
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'phone': user.phone,
                'is_active': user.is_active,
                # Add specialization for doctors
                'specialization': user.specialization.name if user.role == 'doctor' and user.specialization else None
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role,
            'phone': user.phone,
            'gender': user.gender,
            'address': user.address,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'is_active': user.is_active,
            'specialization': user.specialization.name if user.role == 'doctor' and user.specialization else None,
            'qualification': user.qualification if user.role == 'doctor' else None,
            'experience_years': user.experience_years if user.role == 'doctor' else None,
            'consultation_fee': user.consultation_fee if user.role == 'doctor' else None
        }), 200
        
    except Exception as e:
        print(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user'}), 500


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password for current user"""
    data = request.get_json()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new password are required'}), 400
    
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    if not validate_password(data['new_password']):
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200