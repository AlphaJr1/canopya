from enum import Enum
from typing import Dict, Optional
import logging

from src.core.onboarding_messages import get_message, detect_growth_stage
from src.database.base import get_db
from src.database.operations import DatabaseOperations

logger = logging.getLogger(__name__)

class ProfileEditState(Enum):
    VIEW = "view"
    EDIT_NAME = "edit_name"
    EDIT_PLANT = "edit_plant"
    EDIT_STAGE = "edit_stage"
    CONFIRM = "confirm"

class ProfileManager:
    def __init__(self):
        pass
    
    def detect_profile_intent(self, message: str) -> bool:
        """
        Fuzzy matching untuk detect profile intent
        """
        message_lower = message.lower().strip()
        
        profile_keywords = [
            'profil', 'profile', 'data saya', 'info saya', 'lihat data',
            'cek profil', 'my profile', 'my data', 'identitas'
        ]
        
        return any(keyword in message_lower for keyword in profile_keywords)
    
    def detect_edit_intent(self, message: str) -> Optional[str]:
        """
        Detect edit intent dari message
        Returns: 'name', 'plant', 'stage', atau None
        """
        message_lower = message.lower().strip()
        
        if any(kw in message_lower for kw in ['edit nama', 'ganti nama', 'ubah nama', '1']):
            return 'name'
        elif any(kw in message_lower for kw in ['edit tanaman', 'ganti tanaman', 'ubah tanaman', '2']):
            return 'plant'
        elif any(kw in message_lower for kw in ['edit tahap', 'ganti tahap', 'ubah tahap', 'edit stage', '3']):
            return 'stage'
        elif any(kw in message_lower for kw in ['reset', 'onboarding ulang', '4']):
            return 'reset'
        
        return None
    
    def view_profile(self, user_id: str) -> str:
        """
        Tampilkan profil user
        """
        try:
            db = next(get_db())
            db_ops = DatabaseOperations(db)
            
            status = db_ops.get_user_onboarding_status(user_id)
            
            if not status['completed']:
                return "Anda belum menyelesaikan onboarding. Silakan selesaikan dulu!"
            
            data = status['data']
            
            # Format labels
            type_labels = {
                'leafy': 'Sayuran Daun',
                'fruiting': 'Tanaman Buah',
                'herbs': 'Herbal',
                'unknown': 'Lainnya'
            }
            
            stage_labels = {
                'seedling': 'Seedling (Bibit)',
                'vegetative': 'Vegetatif (Tumbuh Daun)',
                'fruiting': 'Berbuah/Berbunga'
            }
            
            return get_message(
                'profile_view',
                full_name=data.get('name', 'N/A'),
                nickname=data.get('nickname', data.get('name', 'N/A')),
                plant_name=data.get('plant_name', 'N/A'),
                plant_type=type_labels.get(data.get('plant_type', 'unknown'), 'Lainnya'),
                growth_stage=stage_labels.get(data.get('growth_stage', 'unknown'), 'N/A')
            )
            
        except Exception as e:
            logger.error(f"Error viewing profile: {e}")
            return "Maaf, terjadi error saat mengambil profil Anda."
    
    def start_edit(self, field: str) -> str:
        """
        Mulai edit flow untuk field tertentu
        """
        if field == 'name':
            return get_message('edit_name_prompt')
        elif field == 'plant':
            return get_message('edit_plant_prompt')
        elif field == 'stage':
            return get_message('edit_stage_prompt')
        else:
            return "Field tidak valid."
    
    def process_edit_input(self, user_id: str, field: str, new_value: str) -> Dict:
        """
        Process input baru untuk edit
        Returns dict dengan old_value, new_value, formatted values
        """
        try:
            db = next(get_db())
            db_ops = DatabaseOperations(db)
            
            status = db_ops.get_user_onboarding_status(user_id)
            data = status['data']
            
            if field == 'name':
                from src.core.onboarding_engine import OnboardingEngine
                engine = OnboardingEngine()
                result = engine._extract_name(new_value)
                
                if not result:
                    return {'error': 'Nama tidak valid. Coba lagi.'}
                
                return {
                    'field': 'Nama',
                    'old_value': data.get('name', 'N/A'),
                    'new_value': result['full_name'],
                    'update_data': {
                        'name': result['full_name'],
                        'nickname': result['nickname']
                    }
                }
            
            elif field == 'plant':
                from src.core.onboarding_engine import OnboardingEngine
                engine = OnboardingEngine()
                plant_name = engine._extract_plant_name(new_value)
                
                if not plant_name:
                    return {'error': 'Nama tanaman tidak valid. Coba lagi.'}
                
                from src.core.onboarding_messages import detect_plant_type
                plant_type = detect_plant_type(plant_name)
                
                return {
                    'field': 'Tanaman',
                    'old_value': data.get('plant_name', 'N/A'),
                    'new_value': plant_name,
                    'update_data': {
                        'plant_name': plant_name,
                        'plant_type': plant_type
                    }
                }
            
            elif field == 'stage':
                growth_stage = detect_growth_stage(new_value)
                
                if growth_stage == 'unknown':
                    return {'error': 'Tahap tidak valid. Pilih: seedling, vegetatif, atau berbuah.'}
                
                stage_labels = {
                    'seedling': 'Seedling (Bibit)',
                    'vegetative': 'Vegetatif (Tumbuh Daun)',
                    'fruiting': 'Berbuah/Berbunga'
                }
                
                return {
                    'field': 'Tahap Pertumbuhan',
                    'old_value': stage_labels.get(data.get('growth_stage', 'unknown'), 'N/A'),
                    'new_value': stage_labels.get(growth_stage, growth_stage),
                    'update_data': {
                        'growth_stage': growth_stage
                    }
                }
            
            return {'error': 'Field tidak dikenali.'}
            
        except Exception as e:
            logger.error(f"Error processing edit: {e}")
            return {'error': 'Terjadi error saat memproses perubahan.'}
    
    def confirm_edit(self, user_id: str, update_data: Dict) -> str:
        """
        Simpan perubahan ke database
        """
        try:
            db = next(get_db())
            db_ops = DatabaseOperations(db)
            
            status = db_ops.get_user_onboarding_status(user_id)
            current_data = status['data']
            
            # Merge update
            current_data.update(update_data)
            
            # Update database
            db_ops.update_onboarding_progress(
                user_id=user_id,
                step=status['step'],
                data_update=current_data
            )
            
            return get_message('edit_success')
            
        except Exception as e:
            logger.error(f"Error confirming edit: {e}")
            return "Maaf, terjadi error saat menyimpan perubahan."
