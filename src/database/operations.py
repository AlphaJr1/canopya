"""
Database Operations Helper - Simplified Version
Support PostgreSQL JSONB untuk conversations

"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import uuid

from .models import User, UserPlant, SensorReading, Message

class DatabaseOperations:
    
    def __init__(self, db: Session):
        self.db = db
    
    
    @staticmethod
    def validate_user_phone(phone_number: str) -> bool:
        """
        Validasi format nomor WhatsApp
        
        Args:
            phone_number: Nomor telepon (format: 62xxx atau +62xxx)
        
        Returns:
            True jika format valid, False jika tidak
        """
        import re
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        
        # Accept formats: 62xxx, +62xxx, 08xxx
        # Convert to 62xxx format
        if phone.startswith("+62"):
            phone = phone[1:]
        elif phone.startswith("08"):
            phone = "62" + phone[1:]
        
        # Validate: must start with 62 and have 10-13 digits total
        pattern = r'^62\d{9,12}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def normalize_phone_number(phone_number: str) -> str:
        """
        Normalize nomor telepon ke format 62xxx
        
        Args:
            phone_number: Nomor telepon dalam berbagai format
        
        Returns:
            Nomor telepon dalam format 62xxx
        """
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        
        if phone.startswith("+62"):
            return phone[1:]
        elif phone.startswith("08"):
            return "62" + phone[1:]
        
        return phone
    
    def get_or_create_user(self, user_id: str, name: Optional[str] = None) -> User:
        user = self.db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            user = User(user_id=user_id, name=name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        elif name and not user.name:
            user.name = name
            self.db.commit()
        
        # Update last_active
        user.last_active = datetime.now()
        self.db.commit()
        
        return user
    
    def update_user_name(self, user_id: str, name: str) -> User:
        user = self.get_or_create_user(user_id)
        user.name = name
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        total_messages = self.db.query(Message).filter(Message.user_id == user_id).count()
        
        # Get all messages and extract unique session_ids (SQLite compatible)
        messages = self.db.query(Message).filter(Message.user_id == user_id).all()
        unique_sessions = set()
        for msg in messages:
            if msg.extra_data and 'session_id' in msg.extra_data:
                unique_sessions.add(msg.extra_data['session_id'])
        
        return {
            'total_messages': total_messages,
            'total_sessions': len(unique_sessions)
        }
    
    def get_all_users(self) -> List[User]:
        """
        Get all users (untuk admin panel)
        
        Returns:
            List of all User objects
        """
        return self.db.query(User).order_by(desc(User.last_active)).all()
    
    def set_user_admin(self, user_id: str, is_admin: bool) -> User:
        """
        Set admin status untuk user
        
        Args:
            user_id: User ID
            is_admin: True untuk set sebagai admin, False untuk remove admin
        
        Returns:
            Updated User object
        """
        user = self.get_or_create_user(user_id)
        user.is_admin = is_admin
        self.db.commit()
        self.db.refresh(user)
        return user
    
    
    def add_plant(
        self, 
        user_id: str, 
        plant_name: str,
        plant_type: Optional[str] = None,
        growth_stage: str = "seedling",
        planting_date: Optional[datetime] = None
    ) -> UserPlant:
        plant = UserPlant(
            user_id=user_id,
            plant_name=plant_name,
            plant_type=plant_type,
            growth_stage=growth_stage,
            planting_date=planting_date or datetime.now().date()
        )
        self.db.add(plant)
        self.db.commit()
        self.db.refresh(plant)
        return plant
    
    def get_active_plants(self, user_id: str) -> List[UserPlant]:
        return self.db.query(UserPlant).filter(
            and_(UserPlant.user_id == user_id, UserPlant.is_active == True)
        ).all()
    
    def update_plant_stage(self, plant_id: int, growth_stage: str) -> UserPlant:
        plant = self.db.query(UserPlant).filter(UserPlant.plant_id == plant_id).first()
        if plant:
            plant.growth_stage = growth_stage
            self.db.commit()
            self.db.refresh(plant)
        return plant
    
    def deactivate_plant(self, plant_id: int) -> UserPlant:
        plant = self.db.query(UserPlant).filter(UserPlant.plant_id == plant_id).first()
        if plant:
            plant.is_active = False
            self.db.commit()
            self.db.refresh(plant)
        return plant
    
    
    def save_sensor_reading(
        self,
        user_id: str,
        ph: Optional[float] = None,
        tds: Optional[float] = None,
        temperature: Optional[float] = None,
        growth_stage: Optional[str] = None,
        plant_id: Optional[int] = None,
        diagnostics: Optional[Dict] = None,
        severity: Optional[str] = None
    ) -> SensorReading:
        
        reading = SensorReading(
            user_id=user_id,
            plant_id=plant_id,
            ph=ph,
            tds=tds,
            temperature=temperature,
            growth_stage=growth_stage,
            severity=severity,
            diagnostics=diagnostics or {}
        )
        
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading
    
    def get_recent_readings(
        self, 
        user_id: str, 
        days: int = 7,
        limit: int = 50
    ) -> List[SensorReading]:
        since = datetime.now() - timedelta(days=days)
        return self.db.query(SensorReading).filter(
            and_(
                SensorReading.user_id == user_id,
                SensorReading.created_at >= since
            )
        ).order_by(desc(SensorReading.created_at)).limit(limit).all()
    
    def get_sensor_trends(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        readings = self.get_recent_readings(user_id, days)
        
        if not readings:
            return {}
        
        # Calculate averages
        ph_values = [float(r.ph) for r in readings if r.ph]
        tds_values = [float(r.tds) for r in readings if r.tds]
        temp_values = [float(r.temperature) for r in readings if r.temperature]
        
        return {
            'total_readings': len(readings),
            'ph': {
                'avg': sum(ph_values) / len(ph_values) if ph_values else None,
                'min': min(ph_values) if ph_values else None,
                'max': max(ph_values) if ph_values else None,
                'count': len(ph_values)
            },
            'tds': {
                'avg': sum(tds_values) / len(tds_values) if tds_values else None,
                'min': min(tds_values) if tds_values else None,
                'max': max(tds_values) if tds_values else None,
                'count': len(tds_values)
            },
            'temperature': {
                'avg': sum(temp_values) / len(temp_values) if temp_values else None,
                'min': min(temp_values) if temp_values else None,
                'max': max(temp_values) if temp_values else None,
                'count': len(temp_values)
            },
            'issues': {
                'critical': len([r for r in readings if r.severity == 'critical']),
                'warning': len([r for r in readings if r.severity == 'warning']),
                'normal': len([r for r in readings if r.severity == 'normal'])
            }
        }
    
    
    def get_or_create_session_id(
        self, 
        user_id: str,
        session_timeout_minutes: int = 30
    ) -> str:
        """
        Get active session ID atau create new one
        Session management via JSON extra_data, tidak perlu table terpisah
        """
        last_message = self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(desc(Message.created_at)).first()
        
        # Check jika session masih valid
        if last_message:
            time_since_last = datetime.now() - last_message.created_at
            
            # Jika gap < timeout dan ada session_id, reuse
            if time_since_last.total_seconds() / 60 < session_timeout_minutes:
                if last_message.extra_data:
                    session_id = last_message.extra_data.get('session_id')
                    if session_id:
                        return session_id
        
        # Create new session ID
        return str(uuid.uuid4())
    
    def save_message(
        self,
        user_id: str,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        sensor_reading_id: Optional[int] = None,
        extra_data: Optional[Dict] = None
    ) -> Message:
        """
        Save message dengan extra_data di JSON
        
        extra_data dapat berisi:
        - session_id: UUID untuk grouping
        - intent: rag/rule_based/hybrid
        - confidence: 0.0-1.0
        - rag_sources: List[str]
        - rag_images: List[str]
        - processing_time_ms: int
        - conversation_context: Dict (topic, resolved, dll)
        """
        if not session_id:
            session_id = self.get_or_create_session_id(user_id)
        
        # Merge session_id ke extra_data
        msg_extra_data = extra_data or {}
        msg_extra_data['session_id'] = session_id
        
        message = Message(
            user_id=user_id,
            role=role,
            content=content,
            sensor_reading_id=sensor_reading_id,
            extra_data=msg_extra_data
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_session_messages(
        self, 
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        # Get all messages for potential session, filter in Python
        all_messages = self.db.query(Message).order_by(Message.created_at).all()
        
        # Filter by session_id in Python (SQLite compatible)
        session_messages = [
            msg for msg in all_messages 
            if msg.extra_data and msg.extra_data.get('session_id') == session_id
        ]
        
        if limit:
            session_messages = session_messages[:limit]
        
        return session_messages
    
    def get_user_sessions(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get user sessions (grouped dari messages) - SQLite compatible
        Returns list of session info
        """
        messages = self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(Message.created_at).all()
        
        # Group by session_id in Python
        sessions_dict = {}
        for msg in messages:
            if not msg.extra_data or 'session_id' not in msg.extra_data:
                continue
            
            session_id = msg.extra_data['session_id']
            
            if session_id not in sessions_dict:
                sessions_dict[session_id] = {
                    'session_id': session_id,
                    'started_at': msg.created_at,
                    'last_message_at': msg.created_at,
                    'message_count': 0,
                    'first_message': msg,
                    'messages': []
                }
            
            sessions_dict[session_id]['last_message_at'] = msg.created_at
            sessions_dict[session_id]['message_count'] += 1
            sessions_dict[session_id]['messages'].append(msg)
        
        # Convert to list and add metadata
        sessions = []
        for session_data in sessions_dict.values():
            first_msg = session_data['first_message']
            primary_intent = first_msg.extra_data.get('intent') if first_msg.extra_data else None
            
            sessions.append({
                'session_id': session_data['session_id'],
                'started_at': session_data['started_at'],
                'last_message_at': session_data['last_message_at'],
                'message_count': session_data['message_count'],
                'primary_intent': primary_intent,
                'is_active': (datetime.now() - session_data['last_message_at']).total_seconds() / 60 < 30
            })
        
        # Sort by last_message_at descending and limit
        sessions.sort(key=lambda x: x['last_message_at'], reverse=True)
        return sessions[:limit]
    
    def get_recent_messages(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Message]:
        return self.db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(desc(Message.created_at)).limit(limit).all()
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user context untuk personalization
        
        Returns:
            Dict dengan user info, plants, recent readings, sessions
        """
        user = self.get_or_create_user(user_id)
        plants = self.get_active_plants(user_id)
        recent_readings = self.get_recent_readings(user_id, days=7)
        trends = self.get_sensor_trends(user_id, days=7)
        sessions = self.get_user_sessions(user_id, limit=5)
        stats = self.get_user_stats(user_id)
        
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
    
    
    def get_user_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user onboarding status
        
        Returns:
            Dict dengan keys: completed, step, data
        """
        user = self.get_or_create_user(user_id)
        
        return {
            'completed': user.onboarding_completed or False,
            'step': user.onboarding_step,
            'data': user.onboarding_data or {}
        }
    
    def update_onboarding_progress(
        self, 
        user_id: str, 
        step: str, 
        data_update: Dict
    ) -> User:
        """
        Update onboarding progress
        
        Args:
            user_id: User ID
            step: Current onboarding step
            data_update: Complete onboarding data (already merged)
        
        Returns:
            Updated User object
        """
        user = self.get_or_create_user(user_id)
        
        # Update step
        user.onboarding_step = step
        
        # Set data directly (already merged in route)
        user.onboarding_data = data_update
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def complete_onboarding(self, user_id: str, final_data: Dict) -> User:
        """
        Mark onboarding as completed and create user plant
        
        Args:
            user_id: User ID
            final_data: Final onboarding data with keys: name, plant_name, plant_type, growth_stage
        
        Returns:
            Updated User object
        """
        user = self.get_or_create_user(user_id)
        
        # Update user name
        if 'name' in final_data:
            user.name = final_data['name']
        
        # Mark onboarding as completed
        user.onboarding_completed = True
        user.onboarding_step = 'completed'
        
        # Clear temporary onboarding data
        user.onboarding_data = {}
        
        self.db.commit()
        
        # Create user plant if data provided
        if 'plant_name' in final_data:
            self.add_plant(
                user_id=user_id,
                plant_name=final_data['plant_name'],
                plant_type=final_data.get('plant_type'),
                growth_stage=final_data.get('growth_stage', 'seedling')
            )
        
        self.db.refresh(user)
        return user
    
    def reset_onboarding(self, user_id: str) -> User:
        """
        Reset onboarding untuk user (untuk testing atau restart)
        
        Args:
            user_id: User ID
        
        Returns:
            Updated User object
        """
        user = self.get_or_create_user(user_id)
        
        user.onboarding_completed = False
        user.onboarding_step = None
        user.onboarding_data = {}
        
        self.db.commit()
        self.db.refresh(user)
        return user

