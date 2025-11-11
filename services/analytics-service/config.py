"""
Configuration module for Analytics Service
Demonstrates: Event-Driven Architecture, Prediction Analytics
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for Analytics Service"""

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@analytics-db:5432/analyticsdb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'

    # RabbitMQ configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

    # Consumer configuration - listens to cycle events
    CYCLE_EXCHANGE = 'cycle_events'
    CYCLE_QUEUE = 'analytics_cycle_queue'
    CYCLE_ROUTING_KEY = 'cycle.#'

    # Publisher configuration - publishes predictions
    PREDICTION_EXCHANGE = 'prediction_events'
    PREDICTION_ROUTING_KEY = 'prediction.new'

    # Service configuration
    SERVICE_NAME = 'analytics-service'
    SERVICE_PORT = 5003
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Analytics configuration
    DEFAULT_CYCLE_LENGTH = 28  # Average cycle length in days
    PREDICTION_WINDOW_DAYS = 3  # Prediction accuracy window
