"""
API Routes for Cycle Tracking Service
Demonstrates: RESTful API, Event Publishing
"""
from flask import Blueprint, request, jsonify
from models import db, Cycle, Symptom
from auth import token_required
from message_queue import get_publisher
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

cycle_bp = Blueprint('cycle', __name__)


@cycle_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'cycle-tracking-service'
    }), 200


@cycle_bp.route('/cycles', methods=['POST'])
@token_required
def create_cycle(user_id):
    """
    Create new menstrual cycle record
    Publishes event to RabbitMQ for analytics service
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'start_date' not in data:
            return jsonify({'error': 'start_date is required'}), 400

        # Create cycle
        cycle = Cycle(
            user_id=user_id,
            start_date=datetime.fromisoformat(data['start_date']).date(),
            end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None
        )

        db.session.add(cycle)
        db.session.commit()

        # Publish event to message queue (Event-Driven Architecture)
        try:
            publisher = get_publisher()
            publisher.publish_cycle_event(cycle.to_dict())
        except Exception as e:
            logger.error(f"Failed to publish cycle event: {str(e)}")
            # Don't fail the request if message publishing fails

        logger.info(f"New cycle created for user {user_id}, cycle_id: {cycle.id}")

        return jsonify({
            'message': 'Cycle created successfully',
            'cycle': cycle.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Cycle creation error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create cycle'}), 500


@cycle_bp.route('/cycles', methods=['GET'])
@token_required
def get_cycles(user_id):
    """
    Get all cycles for authenticated user
    Demonstrates data isolation per user
    """
    try:
        # Optional filters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)

        cycles = Cycle.query.filter_by(user_id=user_id)\
            .order_by(Cycle.start_date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        return jsonify({
            'cycles': [cycle.to_dict() for cycle in cycles],
            'count': len(cycles)
        }), 200

    except Exception as e:
        logger.error(f"Cycles retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve cycles'}), 500


@cycle_bp.route('/cycles/<int:cycle_id>', methods=['GET'])
@token_required
def get_cycle(user_id, cycle_id):
    """Get specific cycle by ID"""
    try:
        cycle = Cycle.query.filter_by(id=cycle_id, user_id=user_id).first()

        if not cycle:
            return jsonify({'error': 'Cycle not found'}), 404

        return jsonify(cycle.to_dict()), 200

    except Exception as e:
        logger.error(f"Cycle retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve cycle'}), 500


@cycle_bp.route('/cycles/<int:cycle_id>', methods=['PUT'])
@token_required
def update_cycle(user_id, cycle_id):
    """
    Update cycle information
    Publishes update event when end_date is added
    """
    try:
        cycle = Cycle.query.filter_by(id=cycle_id, user_id=user_id).first()

        if not cycle:
            return jsonify({'error': 'Cycle not found'}), 404

        data = request.get_json()

        # Update fields
        if 'end_date' in data:
            cycle.end_date = datetime.fromisoformat(data['end_date']).date()

            # Calculate period length
            if cycle.end_date and cycle.start_date:
                cycle.period_length = (cycle.end_date - cycle.start_date).days + 1

        db.session.commit()

        # Publish update event
        try:
            publisher = get_publisher()
            publisher.publish_cycle_event(cycle.to_dict())
        except Exception as e:
            logger.error(f"Failed to publish cycle update event: {str(e)}")

        logger.info(f"Cycle updated: {cycle_id}")

        return jsonify({
            'message': 'Cycle updated successfully',
            'cycle': cycle.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Cycle update error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update cycle'}), 500


@cycle_bp.route('/symptoms', methods=['POST'])
@token_required
def create_symptom(user_id):
    """
    Log symptom/mood for a cycle
    Enriches cycle data for analytics
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['cycle_id', 'date', 'symptom_type', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Verify cycle belongs to user
        cycle = Cycle.query.filter_by(id=data['cycle_id'], user_id=user_id).first()
        if not cycle:
            return jsonify({'error': 'Cycle not found'}), 404

        # Create symptom
        symptom = Symptom(
            cycle_id=data['cycle_id'],
            user_id=user_id,
            date=datetime.fromisoformat(data['date']).date(),
            symptom_type=data['symptom_type'],
            value=data['value'],
            severity=data.get('severity'),
            notes=data.get('notes')
        )

        db.session.add(symptom)
        db.session.commit()

        # Publish event with updated cycle data
        try:
            publisher = get_publisher()
            publisher.publish_cycle_event(cycle.to_dict())
        except Exception as e:
            logger.error(f"Failed to publish symptom event: {str(e)}")

        logger.info(f"New symptom logged for user {user_id}, cycle {data['cycle_id']}")

        return jsonify({
            'message': 'Symptom logged successfully',
            'symptom': symptom.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Symptom creation error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to log symptom'}), 500


@cycle_bp.route('/symptoms', methods=['GET'])
@token_required
def get_symptoms(user_id):
    """Get symptoms for authenticated user"""
    try:
        cycle_id = request.args.get('cycle_id', type=int)

        query = Symptom.query.filter_by(user_id=user_id)

        if cycle_id:
            query = query.filter_by(cycle_id=cycle_id)

        symptoms = query.order_by(Symptom.date.desc()).all()

        return jsonify({
            'symptoms': [symptom.to_dict() for symptom in symptoms],
            'count': len(symptoms)
        }), 200

    except Exception as e:
        logger.error(f"Symptoms retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve symptoms'}), 500
