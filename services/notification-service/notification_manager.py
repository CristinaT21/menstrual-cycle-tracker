"""
Notification Manager
Demonstrates: Notification Logic, Business Rules
"""
from datetime import datetime, timedelta
from models import db, Notification, NotificationPreference
from config import Config
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Handles notification creation and delivery
    Demonstrates service business logic
    """

    @staticmethod
    def create_period_reminder(user_id, prediction_id, predicted_date):
        """
        Create period reminder notification
        Respects user preferences for timing
        """
        try:
            # Get user preferences
            preferences = NotificationPreference.query.filter_by(user_id=user_id).first()

            # Create default preferences if not exist
            if not preferences:
                preferences = NotificationPreference(user_id=user_id)
                db.session.add(preferences)
                db.session.commit()

            # Check if reminders are enabled
            if not preferences.period_reminder_enabled:
                logger.info(f"Period reminders disabled for user {user_id}")
                return None

            # Calculate reminder date
            predicted_datetime = datetime.fromisoformat(predicted_date)
            reminder_date = predicted_datetime - timedelta(days=preferences.reminder_days_before)

            # Create notification
            notification = Notification(
                user_id=user_id,
                prediction_id=prediction_id,
                notification_type='period_reminder',
                title='Period Reminder',
                message=f'Your period is predicted to start in {preferences.reminder_days_before} days (around {predicted_datetime.strftime("%B %d")}). Make sure you are prepared!',
                scheduled_for=reminder_date.date(),
                status='pending'
            )

            db.session.add(notification)
            db.session.commit()

            logger.info(f"Created period reminder for user {user_id}, scheduled for {reminder_date.date()}")

            return notification

        except Exception as e:
            logger.error(f"Failed to create period reminder: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def send_notification(notification):
        """
        Send notification to user
        In production: integrate with email service, push notification service, etc.
        Demonstrates: External Service Integration Point
        """
        try:
            # Simulate notification sending
            # In production, this would call email API, push notification service, etc.

            logger.info(f"[SIMULATED] Sending notification to user {notification.user_id}")
            logger.info(f"[SIMULATED] Type: {notification.notification_type}")
            logger.info(f"[SIMULATED] Title: {notification.title}")
            logger.info(f"[SIMULATED] Message: {notification.message}")

            # Update notification status
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Notification {notification.id} marked as sent")

            return True

        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")

            # Mark as failed
            notification.status = 'failed'
            notification.error_message = str(e)
            db.session.commit()

            return False

    @staticmethod
    def process_pending_notifications():
        """
        Process pending notifications scheduled for today or earlier
        Would be called by a scheduler in production
        """
        try:
            today = datetime.utcnow().date()

            pending_notifications = Notification.query.filter(
                Notification.status == 'pending',
                Notification.scheduled_for <= today
            ).all()

            sent_count = 0
            for notification in pending_notifications:
                if NotificationManager.send_notification(notification):
                    sent_count += 1

            logger.info(f"Processed {sent_count} notifications")

            return sent_count

        except Exception as e:
            logger.error(f"Error processing pending notifications: {str(e)}")
            return 0
