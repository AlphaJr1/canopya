"""
Simulator API Client untuk Chatbot
Poll simulator untuk mendapatkan kondisi sensor terkini

"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SimulatorClient:
    
    def __init__(self, base_url: str = "http://localhost:3456"):
        """
        Initialize simulator client
        Args:
            base_url: Base URL simulator API
        """
        self.base_url = base_url
        self.last_check = None
        self.cached_data = None
        logger.info(f"SimulatorClient initialized with base_url: {base_url}")
    
    def get_current_sensor_data(self) -> Optional[Dict]:
        """
        Get current sensor data dari simulator
        Returns:
            Dict dengan keys: ph, tds, temperature, status, timestamp
            None jika error atau simulator tidak available
        """
        try:
            response = requests.get(
                f"{self.base_url}/current",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.cached_data = data
                self.last_check = datetime.now()
                logger.info(f"Sensor data retrieved: pH={data['ph']}, TDS={data['tds']}, Status={data['status']}")
                return data
            else:
                logger.warning(f"Failed to get sensor data: {response.status_code}")
                return None
        
        except requests.exceptions.ConnectionError:
            logger.debug("Simulator tidak tersedia (connection error)")
            return None
        except Exception as e:
            logger.error(f"Error getting sensor data: {e}")
            return None
    
    def get_insights(self, hours: int = 24) -> Optional[Dict]:
        """
        Get insights dari simulator
        Args:
            hours: Berapa jam ke belakang untuk analisis
        Returns:
            Dict dengan insights atau None
        """
        try:
            response = requests.get(
                f"{self.base_url}/insights",
                params={'hours': hours},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return None
    
    def get_prediction(self) -> Optional[Dict]:
        """
        Get LLM prediction dari simulator
        Returns:
            Dict dengan prediction atau None
        """
        try:
            response = requests.get(
                f"{self.base_url}/predict",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        
        except Exception as e:
            logger.error(f"Error getting prediction: {e}")
            return None
    
    def check_health(self) -> bool:
        """
        Check apakah simulator running
        Returns:
            True jika simulator available
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def format_sensor_status(self, sensor_data: Dict) -> str:
        """
        Format sensor data menjadi string yang readable untuk chatbot context
        Args:
            sensor_data: Dict dari get_current_sensor_data()
        Returns:
            Formatted string
        """
        if not sensor_data:
            return "Data sensor tidak tersedia."
        
        status_desc = {
            'optimal': 'OPTIMAL ✅',
            'warning': 'PERLU PERHATIAN ⚠️',
            'critical': 'KRITIS 🚨'
        }
        
        status = status_desc.get(sensor_data.get('status', 'unknown'), 'UNKNOWN')
        
        lines = [
            f"Kondisi Tanaman: {status}",
            f"pH: {sensor_data.get('ph', 'N/A')}",
            f"TDS: {sensor_data.get('tds', 'N/A')} ppm",
            f"Suhu: {sensor_data.get('temperature', 'N/A')}°C"
        ]
        
        return " | ".join(lines)
    
    def get_context_for_chatbot(self) -> str:
        """
        Get formatted context untuk chatbot - DEPRECATED
        Sensor data sekarang ditangani langsung di hybrid_chatbot.py
        Returns:
            Empty string (fungsi ini tidak digunakan lagi)
        """
        return ""

# Global instance
_simulator_client = None

def get_simulator_client() -> SimulatorClient:
    """
    global _simulator_client
    """
    if _simulator_client is None:
        _simulator_client = SimulatorClient()
    return _simulator_client

if __name__ == "__main__":
    # Test simulator client
    logging.basicConfig(level=logging.INFO)
    
    client = SimulatorClient()
    
    print("Testing Simulator Client...")
    
    # Check health
    print("\n1. Checking simulator health...")
    is_healthy = client.check_health()
    print(f"Simulator status: {'✅ Running' if is_healthy else '❌ Not available'}")
    
    if is_healthy:
        # Get current data
        print("\n2. Getting current sensor data...")
        sensor_data = client.get_current_sensor_data()
        if sensor_data:
            print(f"pH: {sensor_data['ph']}")
            print(f"TDS: {sensor_data['tds']} ppm")
            print(f"Status: {sensor_data['status']}")
        
        # Get formatted status
        print("\n3. Formatted status:")
        print(client.format_sensor_status(sensor_data))
        
        # Get context for chatbot
        print("\n4. Context for chatbot:")
        print(client.get_context_for_chatbot())
    
    print("\nSimulator client test complete!")
