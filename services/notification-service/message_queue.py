"""
RabbitMQ Message Consumer for Notification Service
Demonstrates: Event-Driven Notifications
"""
import pika
import json
import logging
from config import Config
import time
import threading

logger = logging.getLogger(__name__)


class MessageConsumer:
    """
    Consumes prediction events from RabbitMQ
    Triggers notification creation based on events
    """

    def __init__(self, app):
        self.app = app
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        """Establish connection to RabbitMQ"""
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

                # Declare exchange
                self.channel.exchange_declare(
                    exchange=Config.PREDICTION_EXCHANGE,
                    exchange_type='topic',
                    durable=True
                )

                # Declare queue
                self.channel.queue_declare(queue=Config.PREDICTION_QUEUE, durable=True)

                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=Config.PREDICTION_EXCHANGE,
                    queue=Config.PREDICTION_QUEUE,
                    routing_key=Config.PREDICTION_ROUTING_KEY
                )

                logger.info("Consumer connected to RabbitMQ successfully")
                return

            except Exception as e:
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to RabbitMQ after multiple attempts")
                    raise

    def callback(self, ch, method, properties, body):
        """
        Process incoming prediction events
        Creates notifications based on predictions
        """
        try:
            message = json.loads(body)
            logger.info(f"Received prediction event: {message['event_type']}")

            # Process with Flask app context
            with self.app.app_context():
                from notification_manager import NotificationManager

                user_id = message.get('user_id')
                prediction_id = message.get('prediction_id')
                predicted_date = message.get('predicted_start_date')

                # Create period reminder
                notification = NotificationManager.create_period_reminder(
                    user_id=user_id,
                    prediction_id=prediction_id,
                    predicted_date=predicted_date
                )

                if notification:
                    logger.info(f"Created notification for user {user_id}")
                else:
                    logger.warning(f"Failed to create notification for user {user_id}")

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing prediction event: {str(e)}")
            # Reject and don't requeue on error
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """Start consuming messages"""
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=Config.PREDICTION_QUEUE,
                on_message_callback=self.callback
            )

            logger.info("Started consuming prediction events")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error in message consumer: {str(e)}")

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Consumer connection closed")


def start_consumer(app):
    """Start message consumer in background thread"""
    consumer = MessageConsumer(app)
    consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
    consumer_thread.start()
    logger.info("Message consumer thread started")
    return consumer
