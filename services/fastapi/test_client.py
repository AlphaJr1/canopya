"""
Test client untuk Aeropon Chatbot API
Contoh penggunaan API dari Python

"""

import requests
import json
from typing import Dict, Any

class AeroponClient:
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    def chat(
        self,
        message: str,
        language: str = "id",
        include_images: bool = True,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Send message to chatbot
        
        Args:
            message: User message
            language: Response language (id/en)
            include_images: Include images in response
            session_id: Optional session ID for tracking
            
        Returns:
            Chat response dict
        """
        payload = {
            "message": message,
            "language": language,
            "include_images": include_images
        }
        if session_id:
            payload["session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def diagnose(
        self,
        ph: float = None,
        tds: float = None,
        temperature: float = None,
        humidity: float = None,
        growth_stage: str = None
    ) -> Dict[str, Any]:
        """
        Diagnose sensor readings
        
        Args:
            ph: pH value
            tds: TDS/EC value (ppm)
            temperature: Temperature (C)
            humidity: Humidity (%)
            growth_stage: Growth stage (seedling/vegetative/fruiting)
            
        Returns:
            Diagnosis result
        """
        payload = {}
        if ph is not None:
            payload["ph"] = ph
        if tds is not None:
            payload["tds"] = tds
        if temperature is not None:
            payload["temperature"] = temperature
        if humidity is not None:
            payload["humidity"] = humidity
        if growth_stage:
            payload["growth_stage"] = growth_stage
        
        response = self.session.post(
            f"{self.base_url}/diagnose",
            json=payload
        )
        response.raise_for_status()
        return response.json()

def print_response(response: Dict[str, Any], title: str = "Response"):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print(f"{'='*60}\n")

def main():
    """Main test function"""
    print("🤖 Aeropon Chatbot API - Test Client\n")
    
    client = AeroponClient()
    
    # 1. Health Check
    print("1️⃣  Health Check...")
    try:
        health = client.health_check()
        print_response(health, "Health Status")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # 2. Get Stats
    print("2️⃣  Getting Statistics...")
    try:
        stats = client.get_stats()
        print_response(stats, "System Statistics")
    except Exception as e:
        print(f"❌ Stats failed: {e}")
    
    # 3. Test Chat - Knowledge Question
    print("3️⃣  Testing Chat - Knowledge Question...")
    try:
        response = client.chat(
            message="apa kelebihan sistem hidroponik NFT dibanding sistem lainnya?",
            language="id",
            session_id="test-session-1"
        )
        print(f"\n📝 Question: apa kelebihan sistem hidroponik NFT?")
        print(f"🎯 Intent: {response['intent']}")
        print(f"📊 Confidence: {response['confidence']:.2f}")
        print(f"\n💬 Answer:\n{response['answer']}\n")
        
        if response.get('sources'):
            print(f"📚 Sources: {', '.join(response['sources'])}")
        if response.get('num_images', 0) > 0:
            print(f"📸 Images: {response['num_images']}")
    except Exception as e:
        print(f"❌ Chat failed: {e}")
    
    # 4. Test Chat - Sensor Data
    print("\n4️⃣  Testing Chat - Sensor Diagnostics...")
    try:
        response = client.chat(
            message="pH saya 4.5, TDS 1500 ppm, suhu 28°C. Apakah normal?",
            language="id",
            session_id="test-session-2"
        )
        print(f"\n📝 Question: pH 4.5, TDS 1500, suhu 28°C")
        print(f"🎯 Intent: {response['intent']}")
        print(f"📊 Confidence: {response['confidence']:.2f}")
        print(f"🔬 Has Sensor Data: {response['has_sensor_data']}")
        
        if response.get('sensor_data'):
            print(f"\n📡 Detected Sensor Data:")
            for key, value in response['sensor_data'].items():
                if value is not None:
                    print(f"   - {key}: {value}")
        
        print(f"\n💬 Answer:\n{response['answer']}\n")
    except Exception as e:
        print(f"❌ Chat failed: {e}")
    
    # 5. Test Chat - Hybrid (Sensor + How to Fix)
    print("\n5️⃣  Testing Chat - Hybrid Mode...")
    try:
        response = client.chat(
            message="pH saya 4.2, bagaimana cara memperbaikinya?",
            language="id",
            include_images=True,
            session_id="test-session-3"
        )
        print(f"\n📝 Question: pH 4.2, bagaimana cara memperbaikinya?")
        print(f"🎯 Intent: {response['intent']}")
        print(f"📊 Confidence: {response['confidence']:.2f}")
        print(f"\n💬 Answer:\n{response['answer']}\n")
        
        if response.get('images'):
            print(f"📸 Images: {len(response['images'])}")
            for img in response['images']:
                print(f"   - {img}")
    except Exception as e:
        print(f"❌ Chat failed: {e}")
    
    # 6. Test Direct Diagnosis
    print("\n6️⃣  Testing Direct Sensor Diagnosis...")
    try:
        diagnosis = client.diagnose(
            ph=6.5,
            tds=1200,
            temperature=25,
            humidity=65,
            growth_stage="vegetative"
        )
        print(f"\n📡 Sensor Input:")
        print(f"   - pH: 6.5")
        print(f"   - TDS: 1200 ppm")
        print(f"   - Temperature: 25°C")
        print(f"   - Humidity: 65%")
        print(f"   - Growth Stage: vegetative")
        print(f"\n💬 Diagnosis:\n{diagnosis['summary']}\n")
        
        if diagnosis.get('diagnostics'):
            print(f"📊 Detailed Diagnostics:")
            for d in diagnosis['diagnostics']:
                print(f"   - {d['parameter']}: {d['value']} ({d['severity']})")
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
    
    print("\n✅ All tests completed!\n")

if __name__ == "__main__":
    main()
