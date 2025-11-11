"""
User Service - Main Application
Demonstrates: Service Independence, Single Responsibility Principle
"""
from flask import Flask
from models import db
from routes import user_bp
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory pattern for Flask app
    Ensures clean initialization and testability
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api/users')

    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

    logger.info(f"{Config.SERVICE_NAME} started on port {Config.SERVICE_PORT}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=Config.SERVICE_PORT,
        debug=Config.DEBUG
    )
