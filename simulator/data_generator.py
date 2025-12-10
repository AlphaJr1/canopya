"""
Data Generator untuk pH, TDS, dan Temperature
Menggenerate data realistis dengan pola NFT (Nutrient Film Technique)

"""

import json
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class NFTDataGenerator:
    """NFT Data Generator untuk simulasi sensor hidroponik"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize generator dengan config file"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.sensor_ranges = self.config['sensor_ranges']
        self.drift_patterns = self.config['drift_patterns']
        
        # State internal
        self.current_ph = self.sensor_ranges['ph']['initial']
        self.current_tds = self.sensor_ranges['tds']['initial']
        self.current_temp = self.sensor_ranges['temperature']['initial']
        self.start_time = datetime.now()
        self.last_anomaly_time = None
        
        self.daily_drift_ph = 0.0
        self.daily_drift_tds = 0.0
        self.daily_drift_temp = 0.0
        
        self.last_update = datetime.now()
        self.anomaly_active = False
        self.anomaly_end_time = None
        
        logger.info("NFT Data Generator initialized")
        
    
    def get_time_of_day_factor(self) -> float:
        """
        Hitung faktor berdasarkan waktu (diurnal variation)
        Returns nilai antara -1 dan 1
        """
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        # Peak di jam 14:00 (siang), lowest di jam 2:00 (malam)
        return math.sin((hour - 8) * math.pi / 12)
    
    def apply_drift(self, current_value: float, param: str) -> float:
        """
        Apply daily drift pattern
        pH cenderung naik (nutrisi diserap), TDS cenderung turun
        """
        drift_config = self.drift_patterns[param]
        daily_drift = drift_config['daily_drift']
        
        # Drift per 3 menit (180 detik)
        interval_seconds = self.config['data_generation']['interval_seconds']
        drift_per_interval = (daily_drift / 86400) * interval_seconds
        
        return current_value + drift_per_interval
    
    def apply_diurnal_variation(self, base_value: float, param: str) -> float:
        """
        Apply variasi berdasarkan waktu (siang lebih tinggi, malam lebih rendah)
        """
        drift_config = self.drift_patterns[param]
        amplitude = drift_config['diurnal_amplitude']
        time_factor = self.get_time_of_day_factor()
        
        return base_value + (amplitude * time_factor)
    
    def apply_noise(self, value: float, param: str) -> float:
        drift_config = self.drift_patterns[param]
        noise_std = drift_config['noise_std']
        noise = random.gauss(0, noise_std)
        
        return value + noise
    
    def clamp_value(self, value: float, param: str) -> float:
        ranges = self.sensor_ranges[param]
        return max(ranges['min'], min(ranges['max'], value))
    
    def should_inject_anomaly(self) -> bool:
        """
        Decide apakah inject anomali (10% chance)
        Cooldown minimal 1 jam sejak anomali terakhir
        """
        if self.last_anomaly_time:
            time_since_last = datetime.now() - self.last_anomaly_time
            if time_since_last < timedelta(hours=1):
                return False
        
        return random.random() < 0.10
    
    def inject_anomaly(self) -> Dict[str, float]:
        """
        Inject anomali untuk testing
        Returns dict dengan perubahan yang di-apply
        """
        anomaly_types = [
            'ph_spike',
            'ph_drop',
            'tds_spike',
            'tds_drop',
            'temp_spike'
        ]
        
        anomaly = random.choice(anomaly_types)
        changes = {}
        
        if anomaly == 'ph_spike':
            change = random.uniform(0.5, 1.0)
            self.current_ph += change
            changes['ph'] = change
            logger.warning(f"Anomaly injected: pH spike +{change:.2f}")
        
        elif anomaly == 'ph_drop':
            change = random.uniform(0.5, 1.0)
            self.current_ph -= change
            changes['ph'] = -change
            logger.warning(f"Anomaly injected: pH drop -{change:.2f}")
        
        elif anomaly == 'tds_spike':
            change = random.uniform(200, 400)
            self.current_tds += change
            changes['tds'] = change
            logger.warning(f"Anomaly injected: TDS spike +{change:.0f}")
        
        elif anomaly == 'tds_drop':
            change = random.uniform(200, 400)
            self.current_tds -= change
            changes['tds'] = -change
            logger.warning(f"Anomaly injected: TDS drop -{change:.0f}")
        
        elif anomaly == 'temp_spike':
            change = random.uniform(2, 4)
            self.current_temp += change
            changes['temperature'] = change
            logger.warning(f"Anomaly injected: Temperature spike +{change:.1f}")
        
        self.last_anomaly_time = datetime.now()
        return changes
    
    def apply_user_action(self, action_type: str, amount: float = 1.0) -> Dict[str, Tuple[float, float]]:
        """
        Apply user action (gamification)
        Returns dict dengan before/after values
        """
        actions_config = self.config['gamification']['actions']
        
        if action_type not in actions_config:
            raise ValueError(f"Unknown action type: {action_type}")
        
        action = actions_config[action_type]
        
        # Record before values
        ph_before = self.current_ph
        tds_before = self.current_tds
        
        # Apply changes (scaled by amount)
        self.current_ph += action['ph_change'] * amount
        self.current_tds += action['tds_change'] * amount
        
        # Clamp values
        self.current_ph = self.clamp_value(self.current_ph, 'ph')
        self.current_tds = self.clamp_value(self.current_tds, 'tds')
        
        logger.info(f"User action applied: {action_type} (amount={amount})")
        logger.info(f"pH: {ph_before:.2f} -> {self.current_ph:.2f}")
        logger.info(f"TDS: {tds_before:.0f} -> {self.current_tds:.0f}")
        
        return {
            'ph': (ph_before, self.current_ph),
            'tds': (tds_before, self.current_tds)
        }
    
    def generate_next_reading(self) -> Dict:
        """
        Generate reading berikutnya
        Returns dict dengan timestamp, ph, tds, temperature, status
        # Apply drift
        """
        self.current_ph = self.apply_drift(self.current_ph, 'ph')
        self.current_tds = self.apply_drift(self.current_tds, 'tds')
        self.current_temp = self.apply_drift(self.current_temp, 'temperature')
        
        # Apply diurnal variation
        self.current_ph = self.apply_diurnal_variation(self.current_ph, 'ph')
        self.current_tds = self.apply_diurnal_variation(self.current_tds, 'tds')
        self.current_temp = self.apply_diurnal_variation(self.current_temp, 'temperature')
        
        # Apply noise
        self.current_ph = self.apply_noise(self.current_ph, 'ph')
        self.current_tds = self.apply_noise(self.current_tds, 'tds')
        self.current_temp = self.apply_noise(self.current_temp, 'temperature')
        
        # Check anomaly injection
        anomaly_injected = False
        if self.should_inject_anomaly():
            self.inject_anomaly()
            anomaly_injected = True
        
        # Clamp all values
        self.current_ph = self.clamp_value(self.current_ph, 'ph')
        self.current_tds = self.clamp_value(self.current_tds, 'tds')
        self.current_temp = self.clamp_value(self.current_temp, 'temperature')
        
        # Determine status
        status = self._determine_status()
        
        reading = {
            'timestamp': datetime.now().isoformat(),
            'ph': round(self.current_ph, 2),
            'tds': round(self.current_tds, 0),
            'temperature': round(self.current_temp, 1),
            'status': status,
            'anomaly_injected': anomaly_injected,
            'source': 'simulator'
        }
        
        logger.info(f"Generated reading: pH={reading['ph']}, TDS={reading['tds']}, Temp={reading['temperature']}, Status={status}")
        
        return reading
    
    def _determine_status(self) -> str:
        """
        Determine status berdasarkan nilai sensor
        Returns: 'optimal', 'warning', 'critical'
        """
        ph_ranges = self.sensor_ranges['ph']
        tds_ranges = self.sensor_ranges['tds']
        temp_ranges = self.sensor_ranges['temperature']
        alert_thresholds = self.config['gamification']['alert_thresholds']
        
        # Check critical conditions
        if (self.current_ph < alert_thresholds['ph_critical_low'] or 
            self.current_ph > alert_thresholds['ph_critical_high']):
            return 'critical'
        
        if (self.current_tds < alert_thresholds['tds_critical_low'] or 
            self.current_tds > alert_thresholds['tds_critical_high']):
            return 'critical'
        
        # Check warning conditions
        if not (ph_ranges['optimal_min'] <= self.current_ph <= ph_ranges['optimal_max']):
            return 'warning'
        
        if not (tds_ranges['optimal_min'] <= self.current_tds <= tds_ranges['optimal_max']):
            return 'warning'
        
        if not (temp_ranges['optimal_min'] <= self.current_temp <= temp_ranges['optimal_max']):
            return 'warning'
        
        return 'optimal'
    
    def get_current_state(self) -> Dict:
        return {
            'timestamp': datetime.now().isoformat(),
            'ph': round(self.current_ph, 2),
            'tds': round(self.current_tds, 0),
            'temperature': round(self.current_temp, 1),
            'status': self._determine_status(),
            'source': 'simulator'
        }
    
    def reset_to_optimal(self):
        self.current_ph = (self.sensor_ranges['ph']['optimal_min'] + 
                          self.sensor_ranges['ph']['optimal_max']) / 2
        self.current_tds = (self.sensor_ranges['tds']['optimal_min'] + 
                           self.sensor_ranges['tds']['optimal_max']) / 2
        self.current_temp = self.sensor_ranges['temperature']['initial']
        logger.info("Generator reset to optimal values")

if __name__ == "__main__":
    # Test generator
    logging.basicConfig(level=logging.INFO)
    
    generator = NFTDataGenerator()
    
    print("Testing NFT Data Generator...")
    print("\nGenerating 10 readings:")
    for i in range(10):
        reading = generator.generate_next_reading()
        print(f"{i+1}. pH={reading['ph']}, TDS={reading['tds']}, Temp={reading['temperature']}, Status={reading['status']}")
    
    print("\nTesting user action (add_nutrient):")
    result = generator.apply_user_action('add_nutrient')
    print(f"pH: {result['ph'][0]:.2f} -> {result['ph'][1]:.2f}")
    print(f"TDS: {result['tds'][0]:.0f} -> {result['tds'][1]:.0f}")
    
    print("\nCurrent state:")
    state = generator.get_current_state()
    print(json.dumps(state, indent=2))
