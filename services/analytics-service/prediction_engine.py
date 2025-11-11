"""
Prediction Engine for Cycle Analytics
Demonstrates: Business Logic in Domain Service
"""
from datetime import datetime, timedelta
from models import db, CycleAnalytics, Prediction
from config import Config
import logging

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Handles cycle prediction logic
    Demonstrates separation of business logic
    """

    @staticmethod
    def calculate_average_cycle_length(user_id, limit=6):
        """
        Calculate average cycle length for user
        Uses recent cycles for better accuracy
        """
        analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .filter(CycleAnalytics.cycle_length.isnot(None))\
            .order_by(CycleAnalytics.start_date.desc())\
            .limit(limit)\
            .all()

        if not analytics:
            return Config.DEFAULT_CYCLE_LENGTH

        total_length = sum(a.cycle_length for a in analytics)
        return total_length / len(analytics)

    @staticmethod
    def calculate_cycle_variance(user_id, limit=6):
        """
        Calculate variance in cycle lengths
        Helps determine regularity
        """
        analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .filter(CycleAnalytics.cycle_length.isnot(None))\
            .order_by(CycleAnalytics.start_date.desc())\
            .limit(limit)\
            .all()

        if len(analytics) < 2:
            return 0.0

        cycle_lengths = [a.cycle_length for a in analytics]
        mean = sum(cycle_lengths) / len(cycle_lengths)
        variance = sum((x - mean) ** 2 for x in cycle_lengths) / len(cycle_lengths)

        return variance

    @staticmethod
    def predict_next_period(user_id):
        """
        Predict next period start date
        Returns prediction object
        """
        # Get latest cycle
        latest_analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .order_by(CycleAnalytics.start_date.desc())\
            .first()

        if not latest_analytics:
            logger.warning(f"No cycle data found for user {user_id}")
            return None

        # Calculate average cycle length
        avg_cycle_length = PredictionEngine.calculate_average_cycle_length(user_id)
        variance = PredictionEngine.calculate_cycle_variance(user_id)

        # Determine confidence based on regularity
        if variance < 2:
            confidence = 0.9
            is_regular = True
        elif variance < 5:
            confidence = 0.75
            is_regular = True
        else:
            confidence = 0.6
            is_regular = False

        # Predict next start date
        predicted_date = latest_analytics.start_date + timedelta(days=int(avg_cycle_length))

        # Count cycles used
        cycle_count = CycleAnalytics.query.filter_by(user_id=user_id).count()

        # Create prediction
        prediction = Prediction(
            user_id=user_id,
            predicted_start_date=predicted_date,
            confidence_score=confidence,
            prediction_method='average_cycle_length',
            based_on_cycles=min(cycle_count, 6),
            notes=f"Predicted using {min(cycle_count, 6)} recent cycles. Cycle regularity: {'regular' if is_regular else 'irregular'}"
        )

        return prediction

    @staticmethod
    def generate_insights(user_id):
        """
        Generate health insights based on cycle patterns
        Demonstrates analytical capabilities
        """
        insights = []

        # Get cycle analytics
        analytics = CycleAnalytics.query.filter_by(user_id=user_id)\
            .order_by(CycleAnalytics.start_date.desc())\
            .limit(6)\
            .all()

        if len(analytics) < 2:
            insights.append({
                'type': 'info',
                'message': 'Track more cycles for personalized insights'
            })
            return insights

        # Calculate metrics
        avg_cycle_length = PredictionEngine.calculate_average_cycle_length(user_id)
        variance = PredictionEngine.calculate_cycle_variance(user_id)

        # Cycle length insights
        if avg_cycle_length < 21:
            insights.append({
                'type': 'warning',
                'message': 'Your cycles are shorter than average. Consider consulting a healthcare provider.'
            })
        elif avg_cycle_length > 35:
            insights.append({
                'type': 'warning',
                'message': 'Your cycles are longer than average. This may be normal for you, but consider tracking patterns.'
            })
        else:
            insights.append({
                'type': 'positive',
                'message': f'Your average cycle length is {avg_cycle_length:.1f} days, which is within normal range.'
            })

        # Regularity insights
        if variance < 2:
            insights.append({
                'type': 'positive',
                'message': 'Your cycles are very regular, making predictions more accurate.'
            })
        elif variance > 5:
            insights.append({
                'type': 'info',
                'message': 'Your cycles show some variation. This is common and usually normal.'
            })

        # Period length insights
        period_lengths = [a.period_length for a in analytics if a.period_length]
        if period_lengths:
            avg_period_length = sum(period_lengths) / len(period_lengths)
            if avg_period_length > 7:
                insights.append({
                    'type': 'info',
                    'message': 'Your periods last longer than average. If concerned, consult a healthcare provider.'
                })

        return insights
