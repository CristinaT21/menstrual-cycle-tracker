"""
API Routes for Notification Service
Demonstrates: Notification Management, User Preferences
"""
from flask import Blueprint, request, jsonify
from models import db, Notification, NotificationPreference
from auth import token_required
from notification_manager import NotificationManager
import logging

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service'
    }), 200


@notification_bp.route('/preferences', methods=['GET'])
@token_required
def get_preferences(user_id):
    """
    Get notification preferences for user
    """
    try:
        preferences = NotificationPreference.query.filter_by(user_id=user_id).first()

        # Create default preferences if not exist
        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            db.session.add(preferences)
            db.session.commit()

        return jsonify(preferences.to_dict()), 200

    except Exception as e:
        logger.error(f"Preferences retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve preferences'}), 500


@notification_bp.route('/preferences', methods=['PUT'])
@token_required
def update_preferences(user_id):
    """
    Update notification preferences
    Demonstrates user control over notifications
    """
    try:
        preferences = NotificationPreference.query.filter_by(user_id=user_id).first()

        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            db.session.add(preferences)

        data = request.get_json()

        # Update preferences
        if 'period_reminder_enabled' in data:
            preferences.period_reminder_enabled = data['period_reminder_enabled']

        if 'reminder_days_before' in data:
            days = data['reminder_days_before']
            if 1 <= days <= 7:  # Validate range
                preferences.reminder_days_before = days
            else:
                return jsonify({'error': 'reminder_days_before must be between 1 and 7'}), 400

        if 'email_enabled' in data:
            preferences.email_enabled = data['email_enabled']

        if 'push_enabled' in data:
            preferences.push_enabled = data['push_enabled']

        db.session.commit()

        logger.info(f"Updated preferences for user {user_id}")

        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Preferences update error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update preferences'}), 500


@notification_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(user_id):
    """
    Get notifications for user
    Supports filtering by status
    """
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)

        query = Notification.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)

        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications)
        }), 200

    except Exception as e:
        logger.error(f"Notifications retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve notifications'}), 500


@notification_bp.route('/notifications/<int:notification_id>', methods=['GET'])
@token_required
def get_notification(user_id, notification_id):
    """Get specific notification"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        return jsonify(notification.to_dict()), 200

    except Exception as e:
        logger.error(f"Notification retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve notification'}), 500


@notification_bp.route('/notifications/process', methods=['POST'])
def process_notifications():
    """
    Manually trigger processing of pending notifications
    In production, this would be called by a scheduler (cron job)
    """
    try:
        sent_count = NotificationManager.process_pending_notifications()

        return jsonify({
            'message': f'Processed {sent_count} notifications',
            'sent_count': sent_count
        }), 200

    except Exception as e:
        logger.error(f"Notification processing error: {str(e)}")
        return jsonify({'error': 'Failed to process notifications'}), 500
