"""
RabbitMQ Integration for Analytics Service
Demonstrates: Event Consumer and Publisher Pattern
"""
import pika
import json
import logging
from config import Config
import time
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageConsumer:
    """
    Consumes cycle events from RabbitMQ
    Demonstrates event-driven service communication
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
                    exchange=Config.CYCLE_EXCHANGE,
                    exchange_type='topic',
                    durable=True
                )

                # Declare queue
                self.channel.queue_declare(queue=Config.CYCLE_QUEUE, durable=True)

                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=Config.CYCLE_EXCHANGE,
                    queue=Config.CYCLE_QUEUE,
                    routing_key=Config.CYCLE_ROUTING_KEY
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
        Process incoming cycle events
        Updates analytics and generates predictions
        """
        try:
            message = json.loads(body)
            logger.info(f"Received cycle event: {message['event_type']}")

            # Process with Flask app context
            with self.app.app_context():
                from models import db, CycleAnalytics
                from prediction_engine import PredictionEngine
                from datetime import datetime

                cycle_data = message.get('data', {})
                user_id = message.get('user_id')
                cycle_id = message.get('cycle_id')

                # Create or update analytics record
                analytics = CycleAnalytics.query.filter_by(cycle_id=cycle_id).first()

                if not analytics:
                    analytics = CycleAnalytics(
                        user_id=user_id,
                        cycle_id=cycle_id,
                        start_date=datetime.fromisoformat(cycle_data['start_date']).date()
                    )
                    db.session.add(analytics)

                # Update analytics data
                if cycle_data.get('end_date'):
                    analytics.end_date = datetime.fromisoformat(cycle_data['end_date']).date()

                    # Calculate period length
                    if analytics.end_date and analytics.start_date:
                        analytics.period_length = (analytics.end_date - analytics.start_date).days + 1

                # Update analytical metrics
                analytics.average_cycle_length = PredictionEngine.calculate_average_cycle_length(user_id)
                analytics.cycle_variance = PredictionEngine.calculate_cycle_variance(user_id)
                analytics.is_regular = analytics.cycle_variance < 5 if analytics.cycle_variance else None

                # Calculate cycle length if we have previous cycle
                prev_analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
                    .filter(CycleAnalytics.start_date < analytics.start_date)\
                    .order_by(CycleAnalytics.start_date.desc())\
                    .first()

                if prev_analytics:
                    analytics.cycle_length = (analytics.start_date - prev_analytics.start_date).days

                db.session.commit()

                # Generate prediction if we have enough data
                if CycleAnalytics.query.filter_by(user_id=user_id).count() >= 2:
                    prediction = PredictionEngine.predict_next_period(user_id)

                    if prediction:
                        # Deactivate old predictions
                        from models import Prediction
                        Prediction.query.filter_by(user_id=user_id, is_active=True)\
                            .update({'is_active': False})

                        db.session.add(prediction)
                        db.session.commit()

                        # Publish prediction event
                        publisher = MessagePublisher()
                        publisher.publish_prediction(prediction.to_dict())

                logger.info(f"Processed cycle event for user {user_id}")

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing cycle event: {str(e)}")
            # Reject message and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """Start consuming messages"""
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=Config.CYCLE_QUEUE,
                on_message_callback=self.callback
            )

            logger.info("Started consuming cycle events")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error in message consumer: {str(e)}")

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Consumer connection closed")


class MessagePublisher:
    """
    Publishes prediction events
    Demonstrates event publishing for downstream services
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                Config.RABBITMQ_USER,
                Config.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                credentials=credentials
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=Config.PREDICTION_EXCHANGE,
                exchange_type='topic',
                durable=True
            )

            logger.info("Publisher connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Failed to connect publisher: {str(e)}")

    def publish_prediction(self, prediction_data):
        """Publish prediction event for notification service"""
        try:
            if not self.connection or self.connection.is_closed:
                self._connect()

            message = {
                'event_type': 'new_prediction',
                'prediction_id': prediction_data['id'],
                'user_id': prediction_data['user_id'],
                'predicted_start_date': prediction_data['predicted_start_date'],
                'confidence_score': prediction_data['confidence_score'],
                'data': prediction_data
            }

            self.channel.basic_publish(
                exchange=Config.PREDICTION_EXCHANGE,
                routing_key=Config.PREDICTION_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )

            logger.info(f"Published prediction event for user {prediction_data['user_id']}")

        except Exception as e:
            logger.error(f"Failed to publish prediction: {str(e)}")

    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


def start_consumer(app):
    """Start message consumer in background thread"""
    consumer = MessageConsumer(app)
    consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
    consumer_thread.start()
    logger.info("Message consumer thread started")
    return consumer
