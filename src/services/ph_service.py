import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PHService:
    """
    Service untuk fetch pH data dari external APIs
    Support:
    - Real-time pH readings
    - LSTM predictions
    - Mock data fallback
    - Error handling & retry
    """
    
    def __init__(self):
        self.realtime_url = os.getenv(
            "PH_API_REALTIME",
            "https://240d6c5a-085e-4090-9e99-77c9e41ddc06-00-1p1eomiap7bc6.picard.replit.dev/api/get_ph"
        )
        self.predictions_url = os.getenv(
            "PH_API_PREDICTIONS",
            "https://0c72c5e6-c8a2-4c38-af54-30b9ecd07b65-00-xs2kmvkqh478.pike.replit.dev:8080/api/predictions"
        )
        self.timeout = int(os.getenv("PH_API_TIMEOUT", "10"))
        self.use_mock = os.getenv("PH_USE_MOCK_DATA", "false").lower() == "true"
        
        logger.info(f"🌡️ PHService initialized (mock mode: {self.use_mock})")
    
    def get_current_ph(self) -> Dict[str, Any]:
        """
        Get nilai pH real-time terbaru
        
        Returns:
            Dict dengan format:
            {
                "ph": 5.5,
                "timestamp": "2026-01-26 12:30:00",
                "device_id": "68FE7181895C",
                "pompa": "OFF",
                "source": "api" | "mock"
            }
        """
        if self.use_mock:
            return self._get_mock_current_ph()
        
        try:
            logger.info(f"📡 Fetching current pH from {self.realtime_url}")
            response = requests.get(self.realtime_url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Data terbaru ada di index [0]
            if data.get("data") and len(data["data"]) > 0:
                latest = data["data"][0]
                
                result = {
                    "ph": latest.get("ph"),
                    "timestamp": latest.get("timestamp"),
                    "device_id": latest.get("device_id", "UNKNOWN"),
                    "pompa": latest.get("pompa", "UNKNOWN"),
                    "source": "api"
                }
                
                logger.info(f"✅ Got current pH: {result['ph']} at {result['timestamp']}")
                return result
            else:
                logger.warning("⚠️ No data in response, using mock")
                return self._get_mock_current_ph()
        
        except Exception as e:
            logger.error(f"❌ Error fetching current pH: {e}")
            logger.info("🔄 Falling back to mock data")
            return self._get_mock_current_ph()
    
    def get_ph_predictions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get prediksi pH dari LSTM model
        
        Args:
            limit: Berapa banyak prediksi yang diambil (max 20)
            
        Returns:
            List of predictions:
            [{
                "ph": 5.5,
                "timestamp": "2026-01-26 13:00:00",
                "id": 203
            }, ...]
        """
        if self.use_mock:
            return self._get_mock_predictions(limit)
        
        try:
            logger.info(f"📡 Fetching pH predictions from {self.predictions_url}")
            response = requests.get(self.predictions_url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Ambil hanya sejumlah limit
            if isinstance(data, list):
                predictions = data[:limit]
                
                logger.info(f"✅ Got {len(predictions)} predictions")
                return predictions
            else:
                logger.warning("⚠️ Invalid predictions format, using mock")
                return self._get_mock_predictions(limit)
        
        except Exception as e:
            logger.error(f"❌ Error fetching predictions: {e}")
            logger.info("🔄 Falling back to mock predictions")
            return self._get_mock_predictions(limit)
    
    def get_ph_with_predictions(self, prediction_limit: int = 5) -> Dict[str, Any]:
        """
        Get kombinasi pH current + predictions
        
        Args:
            prediction_limit: Berapa banyak prediksi
            
        Returns:
            Dict dengan current dan predictions:
            {
                "current": {...},
                "predictions": [...],
                "trend": "rising" | "falling" | "stable",
                "avg_prediction": 5.6
            }
        """
        current = self.get_current_ph()
        predictions = self.get_ph_predictions(prediction_limit)
        
        # Analisis trend
        if predictions and current.get("ph"):
            current_ph = current["ph"]
            future_ph = predictions[-1]["ph"]  # Last prediction
            
            diff = future_ph - current_ph
            
            if diff > 0.2:
                trend = "rising"
            elif diff < -0.2:
                trend = "falling"
            else:
                trend = "stable"
            
            # Average prediction
            avg_prediction = sum(p["ph"] for p in predictions) / len(predictions)
        else:
            trend = "unknown"
            avg_prediction = None
        
        return {
            "current": current,
            "predictions": predictions,
            "trend": trend,
            "avg_prediction": avg_prediction,
            "prediction_count": len(predictions)
        }
    
    def _get_mock_current_ph(self) -> Dict[str, Any]:
        """Mock data untuk development/testing"""
        return {
            "ph": 5.5,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device_id": "MOCK_DEVICE",
            "pompa": "OFF",
            "source": "mock"
        }
    
    def _get_mock_predictions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Mock predictions untuk development/testing"""
        base_ph = 5.5
        predictions = []
        
        for i in range(limit):
            # Simulasi trend naik perlahan
            ph = base_ph + (i * 0.1)
            predictions.append({
                "id": 200 + i,
                "ph": round(ph, 2),
                "timestamp": f"2026-01-26 {13 + i}:00:00"
            })
        
        return predictions


# Singleton instance
_ph_service_instance: Optional[PHService] = None


def get_ph_service() -> PHService:
    """Get singleton instance of PHService"""
    global _ph_service_instance
    if _ph_service_instance is None:
        _ph_service_instance = PHService()
    return _ph_service_instance


if __name__ == "__main__":
    print("🧪 Testing PHService\n")
    
    service = PHService()
    
    # Test current pH
    print("1️⃣ Testing current pH:")
    current = service.get_current_ph()
    print(f"   pH: {current['ph']}")
    print(f"   Timestamp: {current['timestamp']}")
    print(f"   Source: {current['source']}\n")
    
    # Test predictions
    print("2️⃣ Testing predictions:")
    predictions = service.get_ph_predictions(limit=5)
    for i, pred in enumerate(predictions, 1):
        print(f"   {i}. pH {pred['ph']} at {pred['timestamp']}")
    print()
    
    # Test combined
    print("3️⃣ Testing combined data:")
    combined = service.get_ph_with_predictions(prediction_limit=3)
    print(f"   Current pH: {combined['current']['ph']}")
    print(f"   Trend: {combined['trend']}")
    print(f"   Avg Prediction: {combined['avg_prediction']:.2f}")
    print(f"   Predictions: {len(combined['predictions'])}")
    
    print("\n✅ PHService test complete!")
