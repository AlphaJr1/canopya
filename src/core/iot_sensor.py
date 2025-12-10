"""
IoT Sensor Simulator for NFT Hydroponic System
Simulates realistic sensor readings with configurable trends and anomalies

"""

import random
import json
import time
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class GrowthStage(Enum):
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FRUITING = "fruiting"

class TrendType(Enum):
    STABLE = "stable"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    FLUCTUATING = "fluctuating"

@dataclass
class SensorConfig:
    # Normal ranges
    ph_range: tuple = (5.5, 6.5)
    tds_range: tuple = (800, 1200)  # For vegetative
    temp_range: tuple = (18, 24)
    humidity_range: tuple = (50, 70)
    
    # Variation (±)
    ph_variation: float = 0.3
    tds_variation: float = 100
    temp_variation: float = 2.0
    humidity_variation: float = 5.0
    
    # Anomaly probability (0-1)
    anomaly_probability: float = 0.1

class IoTSensorSimulator:
    
    def __init__(self, growth_stage: GrowthStage = GrowthStage.VEGETATIVE, config: Optional[SensorConfig] = None):
        """
        Initialize sensor simulator
        
        Args:
            growth_stage: Current plant growth stage
            config: Sensor configuration (uses default if None)
        """
        self.growth_stage = growth_stage
        self.config = config or SensorConfig()
        
        # Adjust TDS range based on growth stage
        if growth_stage == GrowthStage.SEEDLING:
            self.config.tds_range = (500, 1000)
        elif growth_stage == GrowthStage.FRUITING:
            self.config.tds_range = (1000, 1500)
        
        # Initial values (center of ranges)
        self.current_ph = sum(self.config.ph_range) / 2
        self.current_tds = sum(self.config.tds_range) / 2
        self.current_temp = sum(self.config.temp_range) / 2
        self.current_humidity = sum(self.config.humidity_range) / 2
        
        # Trends
        self.trends = {
            'ph': TrendType.STABLE,
            'tds': TrendType.STABLE,
            'temp': TrendType.STABLE,
            'humidity': TrendType.STABLE,
        }
    
    def _add_noise(self, value: float, variation: float) -> float:
        noise = random.uniform(-variation, variation)
        return value + noise
    
    def _apply_trend(self, current: float, trend: TrendType, variation: float) -> float:
        if trend == TrendType.STABLE:
            return current + random.uniform(-variation * 0.3, variation * 0.3)
        elif trend == TrendType.INCREASING:
            return current + random.uniform(0, variation * 0.5)
        elif trend == TrendType.DECREASING:
            return current - random.uniform(0, variation * 0.5)
        else:  # FLUCTUATING
            return current + random.uniform(-variation, variation)
    
    def _generate_anomaly(self) -> bool:
        return random.random() < self.config.anomaly_probability
    
    def _constrain(self, value: float, min_val: float, max_val: float, hard_min: float, hard_max: float) -> float:
        # Allow ±20% outside normal range, but hard limits
        if value < hard_min:
            return hard_min
        elif value > hard_max:
            return hard_max
        return value
    
    def read_sensors(self, with_anomaly: bool = False) -> Dict:
        """
        Simulate sensor reading
        
        Args:
            with_anomaly: Force an anomaly (for testing)
            
        Returns:
            Dict with sensor readings
        # Apply trends
        """
        self.current_ph = self._apply_trend(self.current_ph, self.trends['ph'], self.config.ph_variation)
        self.current_tds = self._apply_trend(self.current_tds, self.trends['tds'], self.config.tds_variation)
        self.current_temp = self._apply_trend(self.current_temp, self.trends['temp'], self.config.temp_variation)
        self.current_humidity = self._apply_trend(self.current_humidity, self.trends['humidity'], self.config.humidity_variation)
        
        # Constrain values
        self.current_ph = self._constrain(self.current_ph, *self.config.ph_range, 4.0, 8.0)
        self.current_tds = self._constrain(self.current_tds, *self.config.tds_range, 200, 2500)
        self.current_temp = self._constrain(self.current_temp, *self.config.temp_range, 10, 35)
        self.current_humidity = self._constrain(self.current_humidity, *self.config.humidity_range, 20, 95)
        
        # Generate anomaly if triggered
        if with_anomaly or self._generate_anomaly():
            anomaly_param = random.choice(['ph', 'tds', 'temp', 'humidity'])
            if anomaly_param == 'ph':
                self.current_ph = random.choice([4.0, 4.5, 7.5, 8.0])
            elif anomaly_param == 'tds':
                self.current_tds = random.choice([300, 400, 1800, 2000])
            elif anomaly_param == 'temp':
                self.current_temp = random.choice([14, 15, 28, 30])
            elif anomaly_param == 'humidity':
                self.current_humidity = random.choice([30, 35, 85, 90])
        
        # Add measurement noise
        ph = round(self._add_noise(self.current_ph, 0.1), 1)
        tds = round(self._add_noise(self.current_tds, 20), 0)
        temp = round(self._add_noise(self.current_temp, 0.5), 1)
        humidity = round(self._add_noise(self.current_humidity, 2), 0)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'ph': ph,
            'tds': tds,
            'temperature': temp,
            'humidity': humidity,
            'growth_stage': self.growth_stage.value,
        }
    
    def set_trend(self, parameter: str, trend: TrendType):
        """
        """
        if parameter in self.trends:
            self.trends[parameter] = trend
    
    def simulate_stream(self, duration_seconds: int = 60, interval_seconds: int = 5):
        """
        Simulate sensor stream over time
        
        Args:
            duration_seconds: How long to simulate
            interval_seconds: Reading interval
        print(f"🌱 IoT Sensor Stream - {self.growth_stage.value.upper()} Stage")
        print(f"Duration: {duration_seconds}s, Interval: {interval_seconds}s")
        """
        print("="*70)
        
        start_time = time.time()
        readings = []
        
        while time.time() - start_time < duration_seconds:
            reading = self.read_sensors()
            readings.append(reading)
            
            # Display
            print(f"\n[{reading['timestamp']}]")
            print(f"  pH: {reading['ph']:.1f}")
            print(f"  TDS: {reading['tds']:.0f} ppm")
            print(f"  Temperature: {reading['temperature']:.1f}°C")
            print(f"  Humidity: {reading['humidity']:.0f}%")
            
            time.sleep(interval_seconds)
        
        print("\n" + "="*70)
        print(f"✅ Simulation complete - {len(readings)} readings captured")
        
        return readings

# Preset scenarios for testing
def get_preset_scenario(scenario: str) -> Dict:
    """
    Get preset sensor scenarios
    
    Available scenarios:
    - 'normal': All parameters optimal
    - 'low_ph': Critical low pH
    - 'high_tds': TDS too high  
    - 'heat_stress': High temperature + high humidity
    - 'cold': Low temperature
    - 'random': Random values
    """
    scenarios = {
        'normal': {
            'ph': 6.0,
            'tds': 900,
            'temperature': 22,
            'humidity': 60,
        },
        'low_ph': {
            'ph': 4.2,
            'tds': 1000,
            'temperature': 22,
            'humidity': 60,
        },
        'high_tds': {
            'ph': 6.0,
            'tds': 1800,
            'temperature': 22,
            'humidity': 60,
        },
        'heat_stress': {
            'ph': 6.0,
            'tds': 1000,
            'temperature': 29,
            'humidity': 85,
        },
        'cold': {
            'ph': 6.0,
            'tds': 900,
            'temperature': 14,
            'humidity': 50,
        },
        'random': None,  # Will generate random
    }
    
    if scenario == 'random':
        sim = IoTSensorSimulator()
        return sim.read_sensors()
    
    data = scenarios.get(scenario, scenarios['normal'])
    data['timestamp'] = datetime.now().isoformat()
    data['growth_stage'] = 'vegetative'
    
    return data

if __name__ == "__main__":
    
    print("🔧 IoT Sensor Simulator - Test\n")
    
    # Test 1: Single reading
    print("="*70)
    print("TEST 1: Single Reading (Normal)")
    print("="*70)
    sim = IoTSensorSimulator(growth_stage=GrowthStage.VEGETATIVE)
    reading = sim.read_sensors()
    print(json.dumps(reading, indent=2))
    
    # Test 2: With anomaly
    print("\n" + "="*70)
    print("TEST 2: Single Reading (With Anomaly)")
    print("="*70)
    reading_anomaly = sim.read_sensors(with_anomaly=True)
    print(json.dumps(reading_anomaly, indent=2))
    
    # Test 3: Different growth stages
    print("\n" + "="*70)
    print("TEST 3: Different Growth Stages")
    print("="*70)
    for stage in GrowthStage:
        sim = IoTSensorSimulator(growth_stage=stage)
        reading = sim.read_sensors()
        print(f"\n{stage.value.upper()}:")
        print(f"  TDS: {reading['tds']:.0f} ppm (optimal: {sim.config.tds_range})")
    
    # Test 4: Preset scenarios
    print("\n" + "="*70)
    print("TEST 4: Preset Scenarios")
    print("="*70)
    for scenario in ['normal', 'low_ph', 'high_tds', 'heat_stress']:
        print(f"\n{scenario.upper()}:")
        data = get_preset_scenario(scenario)
        print(f"  pH: {data['ph']}")
        print(f"  TDS: {data['tds']} ppm")
        print(f"  Temp: {data['temperature']}°C")
        print(f"  Humidity: {data['humidity']}%")
    
    print("\n" + "="*70)
    print("✅ Sensor simulator ready!")
    print("\nUsage:")
    print("  from src.core.iot_sensor import IoTSensorSimulator, get_preset_scenario")
    print("  sim = IoTSensorSimulator()")
    print("  reading = sim.read_sensors()")
    print("  # Or use preset:")
    print("  data = get_preset_scenario('low_ph')")
