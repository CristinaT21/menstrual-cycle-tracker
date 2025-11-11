"""
Database models for Analytics Service
Demonstrates: Analytical Data Store, Prediction Tracking
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class CycleAnalytics(db.Model):
    """
    Stores analytical data derived from cycle tracking
    Demonstrates how analytics service maintains its own view of data
    """
    __tablename__ = 'cycle_analytics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    cycle_id = db.Column(db.Integer, nullable=False)  # Reference to cycle in other service

    # Cycle metrics
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    cycle_length = db.Column(db.Integer)
    period_length = db.Column(db.Integer)

    # Analytical insights
    is_regular = db.Column(db.Boolean)
    average_cycle_length = db.Column(db.Float)
    cycle_variance = db.Column(db.Float)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Serialize analytics object"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'cycle_id': self.cycle_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'cycle_length': self.cycle_length,
            'period_length': self.period_length,
            'is_regular': self.is_regular,
            'average_cycle_length': self.average_cycle_length,
            'cycle_variance': self.cycle_variance,
            'created_at': self.created_at.isoformat()
        }


class Prediction(db.Model):
    """
    Stores cycle predictions for users
    Used by notification service to send reminders
    """
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    # Prediction details
    predicted_start_date = db.Column(db.Date, nullable=False)
    confidence_score = db.Column(db.Float)  # 0-1 confidence level
    prediction_method = db.Column(db.String(50))  # e.g., 'average', 'pattern_analysis'

    # Context
    based_on_cycles = db.Column(db.Integer)  # Number of cycles used for prediction
    notes = db.Column(db.Text)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    actual_start_date = db.Column(db.Date)  # Filled when cycle actually starts

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize prediction object"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'predicted_start_date': self.predicted_start_date.isoformat(),
            'confidence_score': self.confidence_score,
            'prediction_method': self.prediction_method,
            'based_on_cycles': self.based_on_cycles,
            'notes': self.notes,
            'is_active': self.is_active,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'created_at': self.created_at.isoformat()
        }
