"""
Authentication utilities for Cycle Tracking Service
Demonstrates: Distributed Authentication with Shared JWT Secret
"""
import jwt
from functools import wraps
from flask import request, jsonify
from config import Config


def decode_token(token):
    """
    Decode and verify JWT token
    Each service can independently verify tokens using shared secret
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """
    Decorator to protect endpoints requiring authentication
    Demonstrates stateless authentication across services
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extract token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        # Verify token
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401

        # Pass user_id to the route
        return f(payload['user_id'], *args, **kwargs)

    return decorated
