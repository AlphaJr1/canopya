"""
Hybrid Chatbot dengan Database Integration
Wrapper untuk HybridChatbot yang menyimpan semua interaksi ke database
"""

from typing import Dict, Optional
import time
from datetime import datetime

from src.core.hybrid_chatbot import HybridChatbot
from src.database.base import get_db
from src.database.operations import DatabaseOperations


class HybridChatbotDB:
    """
    Hybrid Chatbot dengan database persistence
    Menyimpan user profiles, conversations, messages, dan sensor readings
    """
    
    def __init__(self):
        self.chatbot = HybridChatbot()
    
    def chat(
        self, 
        message: str, 
        user_id: str,
        user_name: Optional[str] = None,
        language: str = "id",
        include_images: bool = True,
        session_timeout_minutes: int = 30
    ) -> Dict:
        """
        Main chat function dengan database persistence
        
        Args:
            message: User message
            user_id: User ID (WhatsApp phone number)
            user_name: User name (optional, untuk update profile)
            language: Response language
            include_images: Include images in response
            session_timeout_minutes: Session timeout
            
        Returns:
            Response dict dengan answer, metadata, dan database IDs
        """
        start_time = time.time()
        
        # Get database session
        db = next(get_db())
        ops = DatabaseOperations(db)
        
        try:
            # 1. Get or create user
            user = ops.get_or_create_user(user_id, user_name)
            
            # 2. Get or create session ID (via JSONB, no conversations table)
            session_id = ops.get_or_create_session_id(
                user_id, 
                session_timeout_minutes=session_timeout_minutes
            )
            
            # 3. Save user message
            user_msg = ops.save_message(
                user_id=user_id,
                role="user",
                content=message,
                session_id=session_id
            )
            
            # 4. Process dengan chatbot
            response = self.chatbot.chat(message, language=language, include_images=include_images)
            
            # 5. Save sensor reading jika ada
            sensor_reading_id = None
            if response.get('has_sensor_data') and response.get('sensor_data'):
                sensor_data = response['sensor_data']
                
                # Get active plant (jika ada)
                active_plants = ops.get_active_plants(user_id)
                plant_id = active_plants[0].plant_id if active_plants else None
                
                # Extract diagnostics dari response (jika hybrid/rule_based)
                diagnostics = None
                severity = None
                
                if response['intent'] in ['rule_based', 'hybrid']:
                    # Parse answer untuk extract severity
                    answer_lower = response['answer'].lower()
                    if 'kritis' in answer_lower or 'bahaya' in answer_lower:
                        severity = 'critical'
                    elif 'perhatian' in answer_lower or 'warning' in answer_lower:
                        severity = 'warning'
                    else:
                        severity = 'normal'
                    
                    diagnostics = {
                        'summary': response['answer'][:200],  # First 200 chars
                        'intent': response['intent'],
                        'confidence': response.get('confidence', 0)
                    }
                
                sensor_reading = ops.save_sensor_reading(
                    user_id=user_id,
                    plant_id=plant_id,
                    ph=float(sensor_data.ph) if sensor_data.ph else None,
                    tds=float(sensor_data.tds) if sensor_data.tds else None,
                    temperature=float(sensor_data.temperature) if sensor_data.temperature else None,
                    humidity=float(sensor_data.humidity) if sensor_data.humidity else None,
                    growth_stage=sensor_data.growth_stage.value if sensor_data.growth_stage else None,
                    diagnostics=diagnostics,
                    severity=severity,
                    reading_source="manual"
                )
                sensor_reading_id = sensor_reading.reading_id
            
            # 6. Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 7. Build metadata untuk bot message
            bot_metadata = {
                'session_id': session_id,
                'intent': response.get('intent'),
                'confidence': response.get('confidence'),
                'rag_sources': response.get('sources', []),
                'rag_images': response.get('images', []),
                'processing_time_ms': processing_time_ms
            }
            
            # 8. Save bot response
            bot_msg = ops.save_message(
                user_id=user_id,
                role="bot",
                content=response['answer'],
                session_id=session_id,
                sensor_reading_id=sensor_reading_id,
                extra_data=bot_metadata
            )
            
            # 9. Add database metadata to response
            response['database'] = {
                'user_id': user_id,
                'session_id': session_id,
                'user_message_id': user_msg.message_id,
                'bot_message_id': bot_msg.message_id,
                'sensor_reading_id': sensor_reading_id,
                'processing_time_ms': processing_time_ms
            }
            
            return response
            
        except Exception as e:
            # Log error tapi tetap return response dari chatbot
            print(f"Database error: {e}")
            # Return response tanpa database metadata
            response = self.chatbot.chat(message, language=language, include_images=include_images)
            response['database_error'] = str(e)
            return response
            
        finally:
            db.close()
    
    def get_user_context(self, user_id: str) -> Dict:
        """
        Get user context untuk personalization
        
        Returns:
            Dict dengan user info, plants, recent readings, sessions
        """
        db = next(get_db())
        ops = DatabaseOperations(db)
        
        try:
            user = ops.get_or_create_user(user_id)
            plants = ops.get_active_plants(user_id)
            recent_readings = ops.get_recent_readings(user_id, days=7)
            trends = ops.get_sensor_trends(user_id, days=7)
            sessions = ops.get_user_sessions(user_id, limit=5)
            stats = ops.get_user_stats(user_id)
            
            return {
                'user': {
                    'id': user.user_id,
                    'name': user.name,
                    'total_sessions': stats['total_sessions'],
                    'total_messages': stats['total_messages'],
                    'last_active': user.last_active.isoformat() if user.last_active else None
                },
                'plants': [
                    {
                        'id': p.plant_id,
                        'name': p.plant_name,
                        'type': p.plant_type,
                        'stage': p.growth_stage,
                        'planting_date': p.planting_date.isoformat() if p.planting_date else None
                    }
                    for p in plants
                ],
                'recent_readings': len(recent_readings),
                'sensor_trends': trends,
                'sessions': sessions
            }
        finally:
            db.close()
    
    def add_plant(
        self, 
        user_id: str, 
        plant_name: str,
        plant_type: Optional[str] = None,
        growth_stage: str = "seedling"
    ) -> Dict:
        db = next(get_db())
        ops = DatabaseOperations(db)
        
        try:
            plant = ops.add_plant(
                user_id=user_id,
                plant_name=plant_name,
                plant_type=plant_type,
                growth_stage=growth_stage
            )
            
            return {
                'plant_id': plant.plant_id,
                'plant_name': plant.plant_name,
                'growth_stage': plant.growth_stage
            }
        finally:
            db.close()


def ask_with_db(message: str, user_id: str = "test_user", user_name: str = "Test User") -> str:
    """
    Quick helper untuk testing chatbot dengan database
    
    Usage:
        from src.core.hybrid_chatbot_db import ask_with_db
        response = ask_with_db("pH saya 4.5", "6281234567890", "Budi")
        print(response)
    """
    bot = HybridChatbotDB()
    result = bot.chat(message, user_id, user_name)
    return result['answer']


if __name__ == "__main__":
    
    print("Hybrid Chatbot with Database Test\n")
    
    bot = HybridChatbotDB()
    
    # Test conversation
    user_id = "6281234567890"
    user_name = "Budi Hidroponik"
    
    test_messages = [
        "Halo, saya baru mulai hidroponik",
        "pH saya 4.2, TDS 1500, suhu 28°C",
        "Bagaimana cara menaikkan pH?",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Message {i}: {message}")
        print('='*60)
        
        response = bot.chat(message, user_id, user_name)
        
        print(f"Intent: {response['intent']}")
        print(f"Confidence: {response.get('confidence', 0):.2f}")
        print(f"Processing time: {response['database']['processing_time_ms']}ms")
        print(f"\nResponse:\n{response['answer'][:200]}...")
    
    # Get user context
    print(f"\n{'='*60}")
    print("User Context")
    print('='*60)
    context = bot.get_user_context(user_id)
    print(f"User: {context['user']['name']}")
    print(f"Total messages: {context['user']['total_messages']}")
    print(f"Plants: {len(context['plants'])}")
    print(f"Recent readings: {context['recent_readings']}")
    
    print("\n✅ Test complete")
