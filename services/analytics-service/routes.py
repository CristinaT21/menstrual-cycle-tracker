"""
API Routes for Analytics Service
Demonstrates: Analytical Endpoints, Insights Generation
"""
from flask import Blueprint, request, jsonify
from models import db, CycleAnalytics, Prediction
from auth import token_required
from prediction_engine import PredictionEngine
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'analytics-service'
    }), 200


@analytics_bp.route('/predictions', methods=['GET'])
@token_required
def get_predictions(user_id):
    """
    Get predictions for authenticated user
    Returns active and historical predictions
    """
    try:
        active_only = request.args.get('active', 'true').lower() == 'true'

        query = Prediction.query.filter_by(user_id=user_id)

        if active_only:
            query = query.filter_by(is_active=True)

        predictions = query.order_by(Prediction.created_at.desc()).all()

        return jsonify({
            'predictions': [p.to_dict() for p in predictions],
            'count': len(predictions)
        }), 200

    except Exception as e:
        logger.error(f"Predictions retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve predictions'}), 500


@analytics_bp.route('/predictions/generate', methods=['POST'])
@token_required
def generate_prediction(user_id):
    """
    Manually trigger prediction generation
    Useful for on-demand predictions
    """
    try:
        # Check if user has enough data
        cycle_count = CycleAnalytics.query.filter_by(user_id=user_id).count()

        if cycle_count < 2:
            return jsonify({
                'error': 'Insufficient data for prediction',
                'message': 'At least 2 cycles required for predictions'
            }), 400

        # Generate prediction
        prediction = PredictionEngine.predict_next_period(user_id)

        if not prediction:
            return jsonify({'error': 'Failed to generate prediction'}), 500

        # Deactivate old predictions
        Prediction.query.filter_by(user_id=user_id, is_active=True)\
            .update({'is_active': False})

        db.session.add(prediction)
        db.session.commit()

        # Publish prediction event
        from message_queue import MessagePublisher
        try:
            publisher = MessagePublisher()
            publisher.publish_prediction(prediction.to_dict())
            publisher.close()
        except Exception as e:
            logger.error(f"Failed to publish prediction event: {str(e)}")

        logger.info(f"Generated prediction for user {user_id}")

        return jsonify({
            'message': 'Prediction generated successfully',
            'prediction': prediction.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Prediction generation error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to generate prediction'}), 500


@analytics_bp.route('/insights', methods=['GET'])
@token_required
def get_insights(user_id):
    """
    Get personalized health insights
    Demonstrates analytical capabilities of microservice
    """
    try:
        insights = PredictionEngine.generate_insights(user_id)

        # Get cycle statistics
        analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .order_by(CycleAnalytics.start_date.desc())\
            .limit(6)\
            .all()

        statistics = {
            'total_cycles_tracked': CycleAnalytics.query.filter_by(user_id=user_id).count(),
            'average_cycle_length': None,
            'average_period_length': None,
            'cycle_regularity': 'unknown'
        }

        if analytics:
            # Calculate statistics
            cycle_lengths = [a.cycle_length for a in analytics if a.cycle_length]
            period_lengths = [a.period_length for a in analytics if a.period_length]

            if cycle_lengths:
                statistics['average_cycle_length'] = round(sum(cycle_lengths) / len(cycle_lengths), 1)

            if period_lengths:
                statistics['average_period_length'] = round(sum(period_lengths) / len(period_lengths), 1)

            # Determine regularity
            variance = PredictionEngine.calculate_cycle_variance(user_id)
            if variance < 2:
                statistics['cycle_regularity'] = 'very_regular'
            elif variance < 5:
                statistics['cycle_regularity'] = 'regular'
            else:
                statistics['cycle_regularity'] = 'irregular'

        return jsonify({
            'insights': insights,
            'statistics': statistics
        }), 200

    except Exception as e:
        logger.error(f"Insights generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate insights'}), 500


@analytics_bp.route('/analytics', methods=['GET'])
@token_required
def get_analytics(user_id):
    """
    Get analytical data for user's cycles
    Provides detailed cycle analytics
    """
    try:
        limit = request.args.get('limit', 10, type=int)

        analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .order_by(CycleAnalytics.start_date.desc())\
            .limit(limit)\
            .all()

        return jsonify({
            'analytics': [a.to_dict() for a in analytics],
            'count': len(analytics)
        }), 200

    except Exception as e:
        logger.error(f"Analytics retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500
