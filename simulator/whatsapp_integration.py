"""
WhatsApp Integration Client untuk Simulator
Mengirim alerts dengan interactive buttons ke WhatsApp

"""

import requests
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class WhatsAppClient:
    
    def __init__(self, webhook_url: str = "http://localhost:3000/send-alert"):
        """
        Initialize WhatsApp client
        Args:
            webhook_url: URL WhatsApp webhook endpoint
        """
        self.webhook_url = webhook_url
        logger.info(f"WhatsAppClient initialized with webhook: {webhook_url}")
    
    def send_alert(self, phone_number: str, alert: Dict, buttons: List[Dict] = None) -> bool:
        """
        Send alert dengan optional buttons ke WhatsApp
        
        Args:
            phone_number: Nomor WhatsApp (format: 628xxx)
            alert: Dict dengan keys: type, severity, message, recommended_action
            buttons: Optional list of buttons [{id, text}]
        
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            payload = {
                'phone_number': phone_number,
                'alert': alert,
                'buttons': buttons or []
            }
            
            logger.info(f"Sending alert to {phone_number}: {alert['type']}")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Failed to send alert: {response.status_code} - {response.text}")
                return False
        
        except requests.exceptions.ConnectionError:
            logger.warning("WhatsApp webhook tidak dapat dijangkau (mungkin belum running)")
            return False
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def send_sensor_update(self, phone_number: str, sensor_data: Dict) -> bool:
        """
        Send sensor data update ke WhatsApp
        
        Args:
            phone_number: Nomor WhatsApp
            sensor_data: Dict dengan keys: ph, tds, temperature, status
        
        Returns:
            True jika berhasil
        """
        try:
            # Format message
            message = self._format_sensor_message(sensor_data)
            
            payload = {
                'phone_number': phone_number,
                'message': message,
                'sensor_data': sensor_data
            }
            
            response = requests.post(
                f"{self.webhook_url.replace('/send-alert', '/send-message')}",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Error sending sensor update: {e}")
            return False
    
    def _format_sensor_message(self, sensor_data: Dict) -> str:
        status_emoji = {
            'optimal': '✅',
            'warning': '⚠️',
            'critical': '🚨'
        }
        
        emoji = status_emoji.get(sensor_data.get('status', 'optimal'), 'ℹ️')
        
        lines = [
            f"{emoji} *Update Kondisi Tanaman*",
            "",
            f"📊 pH: {sensor_data.get('ph', 'N/A')}",
            f"💧 TDS: {sensor_data.get('tds', 'N/A')} ppm",
            f"🌡️ Suhu: {sensor_data.get('temperature', 'N/A')}°C",
            f"📈 Status: {sensor_data.get('status', 'N/A').upper()}",
        ]
        
        return "\n".join(lines)
    
    def check_webhook_health(self) -> bool:
        """
        """
        try:
            health_url = self.webhook_url.replace('/send-alert', '/health')
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except:
            return False

if __name__ == "__main__":
    # Test WhatsApp client
    logging.basicConfig(level=logging.INFO)
    
    client = WhatsAppClient()
    
    print("Testing WhatsApp Client...")
    
    # Check health
    print("\n1. Checking webhook health...")
    is_healthy = client.check_webhook_health()
    print(f"Webhook status: {'✅ Running' if is_healthy else '❌ Not available'}")
    
    if not is_healthy:
        print("\n⚠️ WhatsApp webhook tidak running.")
        print("Jalankan dulu: cd whatsapp-webhook && npm start")
    else:
        # Test send alert
        print("\n2. Testing send alert...")
        test_alert = {
            'type': 'ph_high',
            'severity': 'warning',
            'message': 'pH terlalu tinggi (7.2). Target: 5.5-6.5',
            'recommended_action': 'add_ph_down'
        }
        
        test_buttons = [
            {'id': 'action_add_ph_down', 'text': 'Tambah pH Down'},
            {'id': 'action_check_guide', 'text': '📖 Cek Panduan'},
            {'id': 'action_ignore', 'text': '❌ Abaikan'}
        ]
        
        # Note: Ganti dengan nomor WhatsApp yang valid untuk testing
        test_phone = "6281234567890"
        
        success = client.send_alert(test_phone, test_alert, test_buttons)
        print(f"Send alert: {'✅ Success' if success else '❌ Failed'}")
    
    print("\nWhatsApp client test complete!")
