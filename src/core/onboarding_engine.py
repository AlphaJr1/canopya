import re
import logging
from enum import Enum
from typing import Dict, Optional, Tuple
from datetime import datetime

from src.core.onboarding_messages import (
    get_message, detect_plant_type, detect_growth_stage
)

logger = logging.getLogger(__name__)

class OnboardingState(Enum):
    WELCOME = "welcome"
    ASK_NAME = "ask_name"
    ASK_PLANT_NAME = "ask_plant_name"
    ASK_GROWTH_STAGE = "ask_growth_stage"
    CONFIRM_DATA = "confirm_data"
    TUTORIAL = "tutorial"
    COMPLETED = "completed"

class OnboardingEngine:
    def __init__(self):
        pass
    
    def process_message(self, user_data: Dict, message: str) -> Dict:
        current_step = user_data.get('onboarding_step')
        onboarding_data = user_data.get('onboarding_data', {})
        
        if not current_step:
            return self._handle_welcome()
        
        handlers = {
            OnboardingState.WELCOME.value: self._handle_welcome,
            OnboardingState.ASK_NAME.value: self._handle_name_input,
            OnboardingState.ASK_PLANT_NAME.value: self._handle_plant_name_input,
            OnboardingState.ASK_GROWTH_STAGE.value: self._handle_growth_stage_input,
            OnboardingState.CONFIRM_DATA.value: self._handle_confirmation,
            OnboardingState.TUTORIAL.value: self._handle_tutorial,
        }
        
        handler = handlers.get(current_step)
        if handler:
            return handler(message, onboarding_data)
        else:
            logger.warning(f"Unknown onboarding state: {current_step}")
            return self._handle_welcome()
    
    def _handle_welcome(self, message: str = None, data: Dict = None) -> Dict:
        return {
            'response': get_message('welcome'),
            'next_step': OnboardingState.ASK_NAME.value,
            'data_update': {},
            'completed': False
        }
    
    def _handle_name_input(self, message: str, data: Dict) -> Dict:
        # Extract name dari message
        name = self._extract_name(message)
        
        if not name:
            # Invalid name, ask again
            return {
                'response': get_message('follow_up_invalid_name'),
                'next_step': OnboardingState.ASK_NAME.value,
                'data_update': {},
                'completed': False
            }
        
        # Valid name, proceed to ask plant name
        return {
            'response': get_message('ask_plant_name', name=name),
            'next_step': OnboardingState.ASK_PLANT_NAME.value,
            'data_update': {'name': name},
            'completed': False
        }
    
    def _handle_plant_name_input(self, message: str, data: Dict) -> Dict:
        # Extract plant name
        plant_name = self._extract_plant_name(message)
        
        if not plant_name:
            # Invalid plant name, ask again
            return {
                'response': get_message('follow_up_invalid_plant', input=message),
                'next_step': OnboardingState.ASK_PLANT_NAME.value,
                'data_update': {},
                'completed': False
            }
        
        # Auto-detect plant type
        plant_type = detect_plant_type(plant_name)
        
        # Proceed to ask growth stage
        return {
            'response': get_message('ask_growth_stage', plant_name=plant_name),
            'next_step': OnboardingState.ASK_GROWTH_STAGE.value,
            'data_update': {
                'plant_name': plant_name,
                'plant_type': plant_type
            },
            'completed': False
        }
    
    def _handle_growth_stage_input(self, message: str, data: Dict) -> Dict:
        # Detect growth stage
        growth_stage = detect_growth_stage(message)
        
        if growth_stage == 'unknown':
            # Invalid growth stage, ask again
            return {
                'response': get_message('follow_up_invalid_stage'),
                'next_step': OnboardingState.ASK_GROWTH_STAGE.value,
                'data_update': {},
                'completed': False
            }
        
        # Format growth stage untuk display
        stage_labels = {
            'seedling': 'Seedling (Bibit)',
            'vegetative': 'Vegetatif (Tumbuh Daun)',
            'fruiting': 'Berbuah/Berbunga'
        }
        stage_label = stage_labels.get(growth_stage, growth_stage)
        
        # Format plant type untuk display
        type_labels = {
            'leafy': 'Sayuran Daun',
            'fruiting': 'Tanaman Buah',
            'herbs': 'Herbal',
            'unknown': 'Lainnya'
        }
        plant_type_label = type_labels.get(data.get('plant_type', 'unknown'), 'Lainnya')
        
        # Proceed to confirmation
        return {
            'response': get_message(
                'confirm_data',
                name=data.get('name', ''),
                plant_name=data.get('plant_name', ''),
                plant_type=plant_type_label,
                growth_stage=stage_label
            ),
            'next_step': OnboardingState.CONFIRM_DATA.value,
            'data_update': {'growth_stage': growth_stage},
            'completed': False
        }
    
    def _handle_confirmation(self, message: str, data: Dict) -> Dict:
        message_lower = message.lower().strip()
        
        # Check if user confirms
        confirm_keywords = ['ya', 'yes', 'benar', 'betul', 'iya', 'ok', 'oke', 'okay']
        reject_keywords = ['tidak', 'no', 'salah', 'nggak', 'enggak', 'gak']
        
        if any(kw in message_lower for kw in confirm_keywords):
            # User confirms, show tutorial
            return {
                'response': get_message('tutorial'),
                'next_step': OnboardingState.TUTORIAL.value,
                'data_update': {},
                'completed': False
            }
        elif any(kw in message_lower for kw in reject_keywords):
            # User rejects, restart from name
            return {
                'response': get_message('restart_onboarding'),
                'next_step': OnboardingState.ASK_NAME.value,
                'data_update': {},  # Clear previous data
                'completed': False
            }
        else:
            # Unclear response, ask again
            return {
                'response': "Maaf, saya belum paham. Ketik *Ya* jika data sudah benar, atau *Tidak* untuk input ulang.",
                'next_step': OnboardingState.CONFIRM_DATA.value,
                'data_update': {},
                'completed': False
            }
    
    def _handle_tutorial(self, message: str, data: Dict) -> Dict:
        # Tutorial shown, onboarding completed
        return {
            'response': get_message('onboarding_completed'),
            'next_step': OnboardingState.COMPLETED.value,
            'data_update': {},
            'completed': True
        }
    
    def _extract_name(self, message: str) -> Optional[str]:
        """
        Extract name dari user message
        Simple extraction: ambil first 1-3 words, remove common prefixes
        """
        message = re.sub(r'^(nama saya|saya|aku|my name is|i am|i\'m)\s+', '', message, flags=re.IGNORECASE)
        
        # Clean message
        message = message.strip()
        
        # Remove special characters except spaces
        message = re.sub(r'[^a-zA-Z\s]', '', message)
        
        # Take first 1-3 words
        words = message.split()
        if len(words) == 0:
            return None
        
        # Limit to 3 words max (untuk nama panjang)
        name = ' '.join(words[:3])
        
        # Validate: at least 2 characters
        if len(name) < 2:
            return None
        
        # Capitalize properly
        name = name.title()
        
        return name
    
    def _extract_plant_name(self, message: str) -> Optional[str]:
        """
        Extract plant name dari user message
        """
        message = re.sub(r'^(saya tanam|tanam|menanam|tanaman saya|tanaman)\s+', '', message, flags=re.IGNORECASE)
        
        # Clean message
        message = message.strip()
        
        # Remove special characters except spaces
        message = re.sub(r'[^a-zA-Z\s]', '', message)
        
        # Take first 1-2 words
        words = message.split()
        if len(words) == 0:
            return None
        
        plant_name = ' '.join(words[:2])
        
        # Validate: at least 3 characters
        if len(plant_name) < 3:
            return None
        
        # Capitalize properly
        plant_name = plant_name.title()
        
        return plant_name

if __name__ == "__main__":
    # Test onboarding engine
    logging.basicConfig(level=logging.INFO)
    
    engine = OnboardingEngine()
    
    print("Testing Onboarding Engine...\n")
    
    # Simulate user flow
    user_data = {
        'onboarding_step': None,
        'onboarding_data': {}
    }
    
    # Step 1: Welcome
    print("1. Welcome")
    result = engine.process_message(user_data, "")
    print(f"Response: {result['response'][:100]}...")
    print(f"Next step: {result['next_step']}\n")
    
    # Step 2: Name input
    print("2. Name input: 'Budi'")
    user_data['onboarding_step'] = result['next_step']
    result = engine.process_message(user_data, "Budi")
    print(f"Response: {result['response'][:100]}...")
    print(f"Data: {result['data_update']}")
    print(f"Next step: {result['next_step']}\n")
    
    # Step 3: Plant name input
    print("3. Plant name: 'kangkung'")
    user_data['onboarding_step'] = result['next_step']
    user_data['onboarding_data'].update(result['data_update'])
    result = engine.process_message(user_data, "kangkung")
    print(f"Response: {result['response'][:100]}...")
    print(f"Data: {result['data_update']}")
    print(f"Next step: {result['next_step']}\n")
    
    # Step 4: Growth stage
    print("4. Growth stage: 'vegetatif'")
    user_data['onboarding_step'] = result['next_step']
    user_data['onboarding_data'].update(result['data_update'])
    result = engine.process_message(user_data, "vegetatif")
    print(f"Response: {result['response'][:200]}...")
    print(f"Data: {result['data_update']}")
    print(f"Next step: {result['next_step']}\n")
    
    # Step 5: Confirmation
    print("5. Confirmation: 'ya'")
    user_data['onboarding_step'] = result['next_step']
    user_data['onboarding_data'].update(result['data_update'])
    result = engine.process_message(user_data, "ya")
    print(f"Response: {result['response'][:100]}...")
    print(f"Completed: {result['completed']}\n")
    
    print("✅ Onboarding engine test complete!")
