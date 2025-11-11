"""
RabbitMQ Message Queue Integration
Demonstrates: Event-Driven Architecture, Asynchronous Communication
"""
import pika
import json
import logging
from config import Config
import time

logger = logging.getLogger(__name__)


class MessagePublisher:
    """
    Message publisher for publishing cycle events
    Enables loose coupling between services
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        """
        Establish connection to RabbitMQ
        Implements retry logic for resilience
        """
        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                credentials = pika.PlainCredentials(
                    Config.RABBITMQ_USER,
                    Config.RABBITMQ_PASSWORD
                )
                parameters = pika.ConnectionParameters(
                    host=Config.RABBITMQ_HOST,
                    port=Config.RABBITMQ_PORT,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )

                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare exchange (idempotent operation)
                self.channel.exchange_declare(
                    exchange=Config.CYCLE_EXCHANGE,
                    exchange_type='topic',
                    durable=True
                )

                logger.info("Connected to RabbitMQ successfully")
                return

            except Exception as e:
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to RabbitMQ after multiple attempts")
                    raise

    def publish_cycle_event(self, cycle_data):
        """
        Publish new cycle data event
        Other services can subscribe to these events
        """
        try:
            # Ensure connection is alive
            if not self.connection or self.connection.is_closed:
                self._connect()

            message = {
                'event_type': 'new_cycle_data',
                'cycle_id': cycle_data['id'],
                'user_id': cycle_data['user_id'],
                'start_date': cycle_data['start_date'],
                'end_date': cycle_data.get('end_date'),
                'data': cycle_data
            }

            self.channel.basic_publish(
                exchange=Config.CYCLE_EXCHANGE,
                routing_key=Config.CYCLE_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )

            logger.info(f"Published cycle event for cycle_id: {cycle_data['id']}")

        except Exception as e:
            logger.error(f"Failed to publish cycle event: {str(e)}")
            # In production, implement dead letter queue or retry mechanism

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Global publisher instance
publisher = None


def get_publisher():
    """Get or create message publisher instance"""
    global publisher
    if publisher is None:
        publisher = MessagePublisher()
    return publisher
