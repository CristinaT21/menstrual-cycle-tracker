"""
Configuration module for Cycle Tracking Service
Demonstrates: Database-per-Service, Event-Driven Architecture
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for Cycle Tracking Service"""

    # Database configuration - Separate database for this service
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@cycle-db:5432/cycledb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration - Shared secret for token verification
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'

    # RabbitMQ configuration - Message queue for async communication
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

    # Exchange and queue names
    CYCLE_EXCHANGE = 'cycle_events'
    CYCLE_QUEUE = 'new_cycle_data'
    CYCLE_ROUTING_KEY = 'cycle.new'

    # Service configuration
    SERVICE_NAME = 'cycle-tracking-service'
    SERVICE_PORT = 5002
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
