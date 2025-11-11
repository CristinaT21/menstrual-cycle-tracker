"""
Database models for Notification Service
Demonstrates: Notification Management, User Preferences
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class NotificationPreference(db.Model):
    """
    User notification preferences
    Each service manages its own domain data
    """
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True, index=True)

    # Preference settings
    period_reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_days_before = db.Column(db.Integer, default=3)  # Days before predicted date

    # Notification channels (for future expansion)
    email_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Serialize preference object"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period_reminder_enabled': self.period_reminder_enabled,
            'reminder_days_before': self.reminder_days_before,
            'email_enabled': self.email_enabled,
            'push_enabled': self.push_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Notification(db.Model):
    """
    Notification log
    Tracks all notifications sent to users
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    prediction_id = db.Column(db.Integer)  # Reference to prediction

    # Notification details
    notification_type = db.Column(db.String(50), nullable=False)  # e.g., 'period_reminder'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    scheduled_for = db.Column(db.Date, nullable=False)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize notification object"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prediction_id': self.prediction_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'scheduled_for': self.scheduled_for.isoformat(),
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }
