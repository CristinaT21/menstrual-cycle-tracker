"""
API Routes for User Service
Demonstrates: RESTful API Design, Service Autonomy
"""
from flask import Blueprint, request, jsonify
from models import db, User
from auth import generate_token, token_required
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)


@user_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for service monitoring
    Used by orchestration tools to verify service availability
    """
    return jsonify({
        'status': 'healthy',
        'service': 'user-service'
    }), 200


@user_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    Creates new user account with hashed password
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['email', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 409

        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registered: {user.username}")

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    Returns JWT token for authentication across services
    """
    try:
        data = request.get_json()

        # Validate credentials
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403

        # Generate JWT token
        token = generate_token(user.id)

        logger.info(f"User logged in: {user.username}")

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    """
    Get user profile (authenticated endpoint)
    Demonstrates token-based authentication
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500


@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    """
    Update user profile (authenticated endpoint)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'date_of_birth' in data:
            from datetime import datetime
            user.date_of_birth = datetime.fromisoformat(data['date_of_birth']).date()

        db.session.commit()

        logger.info(f"Profile updated: {user.username}")

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user_id, user_id):
    """
    Get user by ID (for inter-service communication)
    Other services can call this to get user information
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    except Exception as e:
        logger.error(f"User retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500
