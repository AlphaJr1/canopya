"""
Database Integration untuk Simulator
CRUD operations dan insights extraction

"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import logging

# Add parent directory to path untuk import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.models import SimulatorReading, UserAction, Prediction
from src.database.base import get_db, engine, Base

logger = logging.getLogger(__name__)

class SimulatorDatabase:
    
    def __init__(self):
        self.ensure_tables_exist()
    
    def ensure_tables_exist(self):
        """
        """
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables ensured")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    
    def save_reading(self, reading_data: Dict) -> SimulatorReading:
        """
        Save sensor reading ke database
        Args:
            reading_data: Dict dengan keys: ph, tds, temperature, status, anomaly_injected, metadata
        Returns:
            SimulatorReading object
        """
        db = next(get_db())
        try:
            reading = SimulatorReading(
                ph=reading_data['ph'],
                tds=reading_data['tds'],
                temperature=reading_data.get('temperature'),
                status=reading_data.get('status', 'optimal'),
                source=reading_data.get('source', 'simulator'),
                anomaly_injected=reading_data.get('anomaly_injected', False),
                extra_metadata=reading_data.get('metadata', {})
            )
            db.add(reading)
            db.commit()
            db.refresh(reading)
            logger.info(f"Saved reading: {reading.reading_id}")
            return reading
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving reading: {e}")
            raise
        finally:
            db.close()
    
    def get_latest_reading(self) -> Optional[SimulatorReading]:
        db = next(get_db())
        try:
            reading = db.query(SimulatorReading).order_by(
                desc(SimulatorReading.created_at)
            ).first()
            return reading
        finally:
            db.close()
    
    def get_readings_since(self, hours: int = 24) -> List[SimulatorReading]:
        """
        Get readings dalam X jam terakhir
        Args:
            hours: Berapa jam ke belakang
        Returns:
            List of SimulatorReading
        """
        db = next(get_db())
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            readings = db.query(SimulatorReading).filter(
                SimulatorReading.created_at >= since_time
            ).order_by(SimulatorReading.created_at).all()
            return readings
        finally:
            db.close()
    
    def get_readings_count(self) -> int:
        db = next(get_db())
        try:
            count = db.query(SimulatorReading).count()
            return count
        finally:
            db.close()
    
    
    def save_action(self, action_data: Dict) -> UserAction:
        """
        Save user action ke database
        Args:
            action_data: Dict dengan keys: user_id, action_type, amount, ph_before, ph_after, tds_before, tds_after, improved_status, context
        Returns:
            UserAction object
        """
        db = next(get_db())
        try:
            action = UserAction(
                user_id=action_data.get('user_id'),
                action_type=action_data['action_type'],
                amount=action_data.get('amount', 1.0),
                ph_before=action_data.get('ph_before'),
                ph_after=action_data.get('ph_after'),
                tds_before=action_data.get('tds_before'),
                tds_after=action_data.get('tds_after'),
                improved_status=action_data.get('improved_status'),
                context=action_data.get('context', {})
            )
            db.add(action)
            db.commit()
            db.refresh(action)
            logger.info(f"Saved action: {action.action_id} - {action.action_type}")
            return action
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving action: {e}")
            raise
        finally:
            db.close()
    
    def get_recent_actions(self, limit: int = 10) -> List[UserAction]:
        db = next(get_db())
        try:
            actions = db.query(UserAction).order_by(
                desc(UserAction.created_at)
            ).limit(limit).all()
            return actions
        finally:
            db.close()
    
    def get_action_stats(self) -> Dict:
        db = next(get_db())
        try:
            total_actions = db.query(UserAction).count()
            successful_actions = db.query(UserAction).filter(
                UserAction.improved_status == True
            ).count()
            
            # Count by action type
            action_counts = db.query(
                UserAction.action_type,
                func.count(UserAction.action_id)
            ).group_by(UserAction.action_type).all()
            
            return {
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'success_rate': successful_actions / total_actions if total_actions > 0 else 0,
                'action_counts': {action_type: count for action_type, count in action_counts}
            }
        finally:
            db.close()
    
    
    def save_prediction(self, prediction_data: Dict) -> Prediction:
        """
        Save LLM prediction ke database
        Args:
            prediction_data: Dict dengan keys: predicted_ph, predicted_tds, prediction_horizon_hours, confidence, recommendation, recommended_action, llm_response, llm_model, historical_data, expires_at
        Returns:
            Prediction object
        """
        db = next(get_db())
        try:
            prediction = Prediction(
                predicted_ph=prediction_data.get('predicted_ph'),
                predicted_tds=prediction_data.get('predicted_tds'),
                prediction_horizon_hours=prediction_data.get('prediction_horizon_hours', 6),
                confidence=prediction_data.get('confidence'),
                recommendation=prediction_data.get('recommendation'),
                recommended_action=prediction_data.get('recommended_action'),
                llm_response=prediction_data.get('llm_response'),
                llm_model=prediction_data.get('llm_model'),
                historical_data=prediction_data.get('historical_data', {}),
                expires_at=prediction_data.get('expires_at')
            )
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            logger.info(f"Saved prediction: {prediction.prediction_id}")
            return prediction
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving prediction: {e}")
            raise
        finally:
            db.close()
    
    def get_latest_prediction(self) -> Optional[Prediction]:
        db = next(get_db())
        try:
            prediction = db.query(Prediction).filter(
                Prediction.expires_at > datetime.now()
            ).order_by(desc(Prediction.created_at)).first()
            return prediction
        finally:
            db.close()
    
    def delete_expired_predictions(self) -> int:
        db = next(get_db())
        try:
            deleted = db.query(Prediction).filter(
                Prediction.expires_at <= datetime.now()
            ).delete()
            db.commit()
            logger.info(f"Deleted {deleted} expired predictions")
            return deleted
        finally:
            db.close()
    
    
    def get_insights(self, hours: int = 24) -> Dict:
        """
        Extract insights dari data
        Args:
            hours: Berapa jam ke belakang untuk analisis
        Returns:
            Dict dengan insights
        """
        readings = self.get_readings_since(hours)
        
        if not readings:
            return {
                'status': 'no_data',
                'message': 'Tidak ada data untuk dianalisis'
            }
        
        # Calculate trends
        ph_values = [r.ph for r in readings]
        tds_values = [r.tds for r in readings]
        
        ph_trend = self._calculate_trend(ph_values)
        tds_trend = self._calculate_trend(tds_values)
        
        # Count anomalies
        anomaly_count = sum(1 for r in readings if r.anomaly_injected)
        
        # Count status distribution
        status_counts = {}
        for r in readings:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
        
        # Latest reading
        latest = readings[-1]
        
        insights = {
            'period_hours': hours,
            'total_readings': len(readings),
            'latest': {
                'ph': float(latest.ph),
                'tds': float(latest.tds),
                'temperature': float(latest.temperature) if latest.temperature else None,
                'status': latest.status,
                'timestamp': latest.created_at.isoformat()
            },
            'trends': {
                'ph': ph_trend,
                'tds': tds_trend
            },
            'anomalies': {
                'count': anomaly_count,
                'percentage': (anomaly_count / len(readings)) * 100
            },
            'status_distribution': status_counts,
            'alerts': self._generate_alerts(latest, ph_trend, tds_trend)
        }
        
        return insights
    
    def _calculate_trend(self, values: List[float]) -> Dict:
        """
        """
        if len(values) < 2:
            return {'direction': 'stable', 'change': 0}
        
        # Convert to float to avoid Decimal issues
        values = [float(v) for v in values]
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine direction
        if abs(slope) < 0.01:  # Threshold untuk "stable"
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        change = values[-1] - values[0]
        
        return {
            'direction': direction,
            'slope': round(slope, 4),
            'change': round(change, 2),
            'start_value': round(values[0], 2),
            'end_value': round(values[-1], 2)
        }
    
    def _generate_alerts(self, latest: SimulatorReading, ph_trend: Dict, tds_trend: Dict) -> List[Dict]:
        alerts = []
        
        # pH alerts
        if latest.ph < 5.5:
            alerts.append({
                'type': 'ph_low',
                'severity': 'critical' if latest.ph < 5.0 else 'warning',
                'message': f'pH terlalu rendah ({latest.ph}). Target: 5.5-6.5',
                'recommended_action': 'add_ph_up'
            })
        elif latest.ph > 6.5:
            alerts.append({
                'type': 'ph_high',
                'severity': 'critical' if latest.ph > 7.5 else 'warning',
                'message': f'pH terlalu tinggi ({latest.ph}). Target: 5.5-6.5',
                'recommended_action': 'add_ph_down'
            })
        
        # TDS alerts
        if latest.tds < 800:
            alerts.append({
                'type': 'tds_low',
                'severity': 'critical' if latest.tds < 600 else 'warning',
                'message': f'TDS terlalu rendah ({latest.tds} ppm). Target: 800-1400 ppm',
                'recommended_action': 'add_nutrient'
            })
        elif latest.tds > 1400:
            alerts.append({
                'type': 'tds_high',
                'severity': 'critical' if latest.tds > 1800 else 'warning',
                'message': f'TDS terlalu tinggi ({latest.tds} ppm). Target: 800-1400 ppm',
                'recommended_action': 'add_water'
            })
        
        # Trend alerts
        if ph_trend['direction'] == 'increasing' and ph_trend['slope'] > 0.05:
            alerts.append({
                'type': 'ph_rising_fast',
                'severity': 'warning',
                'message': f'pH naik cepat (+{ph_trend["change"]} dalam {ph_trend.get("period", "periode terakhir")})',
                'recommended_action': 'monitor'
            })
        
        if tds_trend['direction'] == 'decreasing' and abs(tds_trend['slope']) > 5:
            alerts.append({
                'type': 'tds_dropping_fast',
                'severity': 'warning',
                'message': f'TDS turun cepat ({tds_trend["change"]} ppm dalam {tds_trend.get("period", "periode terakhir")})',
                'recommended_action': 'add_nutrient'
            })
        
        return alerts

if __name__ == "__main__":
    # Test database operations
    logging.basicConfig(level=logging.INFO)
    
    db = SimulatorDatabase()
    
    print("Testing database operations...")
    
    # Test save reading
    print("\n1. Saving test reading...")
    reading_data = {
        'ph': 6.2,
        'tds': 1150,
        'temperature': 26.5,
        'status': 'optimal',
        'anomaly_injected': False,
        'metadata': {'test': True}
    }
    reading = db.save_reading(reading_data)
    print(f"Saved: {reading}")
    
    # Test get latest
    print("\n2. Getting latest reading...")
    latest = db.get_latest_reading()
    print(f"Latest: {latest}")
    
    # Test get insights
    print("\n3. Getting insights...")
    insights = db.get_insights(hours=24)
    print(json.dumps(insights, indent=2, default=str))
    
    print("\nDatabase operations test complete!")
