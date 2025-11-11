"""
Configuration module for User Service
Demonstrates: Externalized Configuration Pattern
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for User Service"""

    # Database configuration - Database-per-Service Pattern
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@user-db:5432/userdb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration - Shared Secret for Inter-Service Authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

    # Service configuration
    SERVICE_NAME = 'user-service'
    SERVICE_PORT = 5001
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
