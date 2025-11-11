"""
Database models for Cycle Tracking Service
Demonstrates: Domain-Driven Design, Service Data Ownership
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Cycle(db.Model):
    """
    Menstrual cycle record
    Each service owns its domain data
    """
    __tablename__ = 'cycles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    # Cycle dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)

    # Cycle characteristics
    cycle_length = db.Column(db.Integer)  # Days between start of this cycle and next
    period_length = db.Column(db.Integer)  # Duration of bleeding

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    symptoms = db.relationship('Symptom', backref='cycle', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Serialize cycle object"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'cycle_length': self.cycle_length,
            'period_length': self.period_length,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'symptoms': [symptom.to_dict() for symptom in self.symptoms]
        }


class Symptom(db.Model):
    """
    Symptom/mood tracking for a specific cycle
    Supports rich cycle data collection
    """
    __tablename__ = 'symptoms'

    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('cycles.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    # Symptom details
    date = db.Column(db.Date, nullable=False)
    symptom_type = db.Column(db.String(50), nullable=False)  # e.g., 'mood', 'pain', 'flow'
    value = db.Column(db.String(100), nullable=False)  # e.g., 'happy', 'cramping', 'heavy'
    severity = db.Column(db.Integer)  # 1-10 scale
    notes = db.Column(db.Text)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize symptom object"""
        return {
            'id': self.id,
            'cycle_id': self.cycle_id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'symptom_type': self.symptom_type,
            'value': self.value,
            'severity': self.severity,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
