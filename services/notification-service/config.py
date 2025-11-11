"""
Configuration module for Notification Service
Demonstrates: Event-Driven Notifications, Service Autonomy
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration for Notification Service"""

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@notification-db:5432/notificationdb'
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

    # Consumer configuration - listens to prediction events
    PREDICTION_EXCHANGE = 'prediction_events'
    PREDICTION_QUEUE = 'notification_prediction_queue'
    PREDICTION_ROUTING_KEY = 'prediction.#'

    # Service configuration
    SERVICE_NAME = 'notification-service'
    SERVICE_PORT = 5004
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Notification configuration
    DEFAULT_REMINDER_DAYS = 3  # Days before predicted period to send reminder
