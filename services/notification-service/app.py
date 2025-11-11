"""
Notification Service - Main Application
Demonstrates: Event-Driven Notifications, Asynchronous Processing
"""
from flask import Flask
from models import db
from routes import notification_bp
from config import Config
from message_queue import start_consumer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory for Notification Service"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')

    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

    # Start message consumer in background
    try:
        start_consumer(app)
        logger.info("Message consumer started")
    except Exception as e:
        logger.error(f"Failed to start message consumer: {str(e)}")

    logger.info(f"{Config.SERVICE_NAME} started on port {Config.SERVICE_PORT}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=Config.SERVICE_PORT,
        debug=Config.DEBUG
    )
