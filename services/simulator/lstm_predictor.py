"""
LLM-based Predictor menggunakan Qwen2.5:7b-instruct via Ollama
Analisis trend dan generate rekomendasi aksi

"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class LLMPredictor:
    """LLM-based Predictor menggunakan Qwen2.5:7b-instruct"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize LLM predictor dengan config file"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.llm_config = self.config['llm']
        self.base_url = self.llm_config['base_url']
        self.model = self.llm_config['model']
        self.temperature = self.llm_config['temperature']
        self.max_tokens = self.llm_config['max_tokens']
        
        self.cached_prediction = None
        self.cache_expires_at = None
        
        logger.info(f"LLMPredictor initialized with model: {self.model}")
    
    def _check_ollama_health(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call Ollama API
        Args:
            prompt: Prompt untuk LLM
        Returns:
            Response text atau None jika error
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None
    
    def _format_historical_data(self, readings: List) -> str:
        """
        Format historical data untuk prompt
        Args:
            readings: List of SimulatorReading objects
        Returns:
            Formatted string
        """
        if not readings:
            return "Tidak ada data historis."
        
        # Group by day
        data_by_day = {}
        for r in readings:
            day = r.created_at.date()
            if day not in data_by_day:
                data_by_day[day] = []
            data_by_day[day].append({
                'time': r.created_at.strftime('%H:%M'),
                'ph': float(r.ph),
                'tds': float(r.tds),
                'status': r.status
            })
        
        # Format untuk prompt
        lines = []
        for day in sorted(data_by_day.keys()):
            day_readings = data_by_day[day]
            
            # Calculate daily averages
            avg_ph = sum(r['ph'] for r in day_readings) / len(day_readings)
            avg_tds = sum(r['tds'] for r in day_readings) / len(day_readings)
            
            # Count status
            status_counts = {}
            for r in day_readings:
                status_counts[r['status']] = status_counts.get(r['status'], 0) + 1
            
            lines.append(f"Tanggal {day}:")
            lines.append(f"  - Rata-rata pH: {avg_ph:.2f}")
            lines.append(f"  - Rata-rata TDS: {avg_tds:.0f} ppm")
            lines.append(f"  - Status: {status_counts}")
            lines.append(f"  - Total pembacaan: {len(day_readings)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_prompt(self, historical_data_str: str, latest_reading: Dict) -> str:
        """
        Build prompt untuk LLM
        Args:
            historical_data_str: Formatted historical data
            latest_reading: Dict dengan latest reading
        Returns:
            Prompt string
        """
        prompt = f"""Kamu adalah AI expert untuk sistem hidroponik NFT (Nutrient Film Technique).

**Data Historis (7 hari terakhir):**
{historical_data_str}

**Pembacaan Terkini:**
- pH: {latest_reading['ph']}
- TDS: {latest_reading['tds']} ppm
- Temperature: {latest_reading.get('temperature', 'N/A')}°C
- Status: {latest_reading['status']}
- Waktu: {latest_reading['timestamp']}

**Target Optimal:**
- pH: 5.5 - 6.5
- TDS: 800 - 1400 ppm

**Instruksi:**
1. Analisis trend pH dan TDS dari data historis
2. Prediksi nilai pH dan TDS untuk 6 jam ke depan
3. Berikan rekomendasi aksi yang spesifik dan actionable
4. Jelaskan alasan di balik rekomendasi

**Format Response (JSON):**
{{
  "trend_analysis": {{
    "ph": "penjelasan trend pH (naik/turun/stabil dan alasannya)",
    "tds": "penjelasan trend TDS (naik/turun/stabil dan alasannya)"
  }},
  "prediction_6h": {{
    "ph": <nilai prediksi pH>,
    "tds": <nilai prediksi TDS>
  }},
  "confidence": <0.0-1.0>,
  "recommendation": {{
    "action": "add_nutrient|add_water|add_ph_down|add_ph_up|monitor",
    "reason": "penjelasan mengapa action ini direkomendasikan",
    "urgency": "low|medium|high"
  }},
  "summary": "ringkasan singkat kondisi dan rekomendasi dalam 1-2 kalimat"
}}
"""
        return prompt
    
    def predict(self, historical_readings: List, latest_reading: Dict, force_refresh: bool = False) -> Optional[Dict]:
        """
        Generate prediction dan recommendation
        Args:
            historical_readings: List of SimulatorReading objects (7 hari terakhir)
            latest_reading: Dict dengan latest reading
            force_refresh: Force refresh cache
        Returns:
            Dict dengan prediction atau None jika error
        """
        if not force_refresh and self.cached_prediction and self.cache_expires_at:
            if datetime.now() < self.cache_expires_at:
                logger.info("Returning cached prediction")
                return self.cached_prediction
        
        # Check Ollama health
        if not self._check_ollama_health():
            logger.error("Ollama server not available")
            return None
        
        # Format historical data
        historical_data_str = self._format_historical_data(historical_readings)
        
        # Build prompt
        prompt = self._build_prompt(historical_data_str, latest_reading)
        
        # Call LLM
        logger.info("Calling LLM for prediction...")
        llm_response = self._call_ollama(prompt)
        
        if not llm_response:
            logger.error("Failed to get LLM response")
            return None
        
        # Parse response
        try:
            # Extract JSON from response (LLM might add extra text)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in LLM response")
                return None
            
            json_str = llm_response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Build result
            result = {
                'predicted_ph': parsed['prediction_6h']['ph'],
                'predicted_tds': parsed['prediction_6h']['tds'],
                'prediction_horizon_hours': 6,
                'confidence': parsed['confidence'],
                'recommendation': parsed['recommendation']['reason'],
                'recommended_action': parsed['recommendation']['action'],
                'urgency': parsed['recommendation']['urgency'],
                'trend_analysis': parsed['trend_analysis'],
                'summary': parsed['summary'],
                'llm_response': llm_response,
                'llm_model': self.model,
                'created_at': datetime.now().isoformat(),
                'historical_data': {
                    'readings_count': len(historical_readings),
                    'date_range': {
                        'start': historical_readings[0].created_at.isoformat() if historical_readings else None,
                        'end': historical_readings[-1].created_at.isoformat() if historical_readings else None
                    }
                }
            }
            
            # Cache result
            cache_duration = self.llm_config['cache_duration_minutes']
            self.cached_prediction = result
            self.cache_expires_at = datetime.now() + timedelta(minutes=cache_duration)
            
            logger.info(f"Prediction generated successfully (confidence: {result['confidence']})")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {llm_response}")
            return None
        except KeyError as e:
            logger.error(f"Missing key in LLM response: {e}")
            return None
    
    def get_cached_prediction(self) -> Optional[Dict]:
        """Get cached prediction if still valid"""
        if self.cached_prediction and self.cache_expires_at:
            if datetime.now() < self.cache_expires_at:
                return self.cached_prediction
        return None
    
    def clear_cache(self):
        self.cached_prediction = None
        self.cache_expires_at = None
        logger.info("Prediction cache cleared")

if __name__ == "__main__":
    # Test LLM predictor
    logging.basicConfig(level=logging.INFO)
    
    predictor = LLMPredictor()
    
    print("Testing LLM Predictor...")
    
    # Check Ollama health
    print("\n1. Checking Ollama health...")
    health = predictor._check_ollama_health()
    print(f"Ollama status: {'✅ Running' if health else '❌ Not available'}")
    
    if not health:
        print("\n⚠️ Ollama tidak running. Pastikan Ollama sudah dijalankan di localhost:11434")
        print("Jalankan: ollama serve")
        exit(1)
    
    # Test dengan dummy data
    print("\n2. Testing prediction dengan dummy data...")
    
    # Create dummy historical readings
    class DummyReading:
        """Dummy reading class for testing"""
        def __init__(self, ph, tds, created_at, status='optimal'):
            self.ph = ph
            self.tds = tds
            self.created_at = created_at
            self.status = status
    
    historical_readings = [
        DummyReading(6.0, 1200, datetime.now() - timedelta(days=7)),
        DummyReading(6.1, 1180, datetime.now() - timedelta(days=6)),
        DummyReading(6.3, 1150, datetime.now() - timedelta(days=5)),
        DummyReading(6.5, 1120, datetime.now() - timedelta(days=4)),
        DummyReading(6.7, 1090, datetime.now() - timedelta(days=3)),
        DummyReading(6.9, 1050, datetime.now() - timedelta(days=2)),
        DummyReading(7.1, 1020, datetime.now() - timedelta(days=1), status='warning'),
    ]
    
    latest_reading = {
        'ph': 7.2,
        'tds': 1000,
        'temperature': 26.5,
        'status': 'warning',
        'timestamp': datetime.now().isoformat()
    }
    
    prediction = predictor.predict(historical_readings, latest_reading)
    
    if prediction:
        print("\n✅ Prediction berhasil!")
        print(f"\nPrediksi 6 jam ke depan:")
        print(f"  pH: {prediction['predicted_ph']}")
        print(f"  TDS: {prediction['predicted_tds']} ppm")
        print(f"\nConfidence: {prediction['confidence']}")
        print(f"\nRekomendasi: {prediction['recommended_action']}")
        print(f"Alasan: {prediction['recommendation']}")
        print(f"Urgency: {prediction['urgency']}")
        print(f"\nSummary: {prediction['summary']}")
    else:
        print("\n❌ Prediction gagal")
    
    print("\nLLM predictor test complete!")
