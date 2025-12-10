"""
Simplified SQLAlchemy Models untuk Aeropon Chatbot Database
PostgreSQL + JSONB - Hapus semua NICE-TO-HAVE fields
SQLite fallback: uses JSON instead of JSONB

"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, 
    DateTime, Date, ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from .base import Base, engine

# Use JSONB for PostgreSQL, JSON for SQLite
if engine.dialect.name == 'postgresql':
    JSONType = JSONB
else:
    JSONType = JSON  # SQLite fallback

class User(Base):
    __tablename__ = "users"
    
    # CRITICAL fields only
    user_id = Column(String(50), primary_key=True)  # WhatsApp phone number
    name = Column(String(100))  # Personalisasi
    last_active = Column(DateTime, default=func.now(), onupdate=func.now())  # Session management
    created_at = Column(DateTime, default=func.now())  # Keep for basic tracking
    
    # Onboarding fields
    onboarding_completed = Column(Boolean, default=False)  # Track if user completed onboarding
    onboarding_step = Column(String(50))  # Current step: welcome, ask_name, ask_plant_name, etc
    onboarding_data = Column(JSONType, default=dict)  # Temporary data during onboarding
    
    # Admin access
    is_admin = Column(Boolean, default=False)  # Admin access untuk dashboard monitoring
    
    # Relationships
    plants = relationship("UserPlant", back_populates="user", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, name={self.name})>"

class UserPlant(Base):
    __tablename__ = "user_plants"
    
    # CRITICAL & IMPORTANT fields
    plant_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    plant_name = Column(String(100), nullable=False)  # CRITICAL
    plant_type = Column(String(50))  # IMPORTANT: leafy/fruiting/herbs
    growth_stage = Column(String(20))  # CRITICAL: optimal ranges berbeda!
    planting_date = Column(Date)  # IMPORTANT: auto-detect stage
    is_active = Column(Boolean, default=True)  # IMPORTANT: filter
    
    # Relationships
    user = relationship("User", back_populates="plants")
    sensor_readings = relationship("SensorReading", back_populates="plant")
    
    def __repr__(self):
        return f"<UserPlant(plant_id={self.plant_id}, name={self.plant_name}, stage={self.growth_stage})>"

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    # IDs
    reading_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(Integer, ForeignKey("user_plants.plant_id", ondelete="SET NULL"))
    
    # CRITICAL sensor values
    ph = Column(Numeric(4, 2))  # Core parameter
    tds = Column(Numeric(7, 2))  # Core parameter (PPM)
    temperature = Column(Numeric(4, 2))  # IMPORTANT: affects nutrient uptake
    
    # CRITICAL context
    growth_stage = Column(String(20))  # Snapshot saat reading - CRITICAL!
    severity = Column(String(20))  # IMPORTANT: normal/warning/critical
    
    # JSONB for flexibility - diagnostics dari rule engine
    diagnostics = Column(JSONType, default=dict)  # Full diagnostic result
    
    # CRITICAL timestamp
    created_at = Column(DateTime, default=func.now())  # Time-series analysis
    
    # Relationships
    user = relationship("User", back_populates="sensor_readings")
    plant = relationship("UserPlant", back_populates="sensor_readings")
    messages = relationship("Message", back_populates="sensor_reading")
    
    def __repr__(self):
        return f"<SensorReading(id={self.reading_id}, pH={self.ph}, TDS={self.tds}, severity={self.severity})>"

class Message(Base):
    """
    Messages - Simplified dengan JSONB untuk conversation context
    Conversations tidak perlu table terpisah - group by session_id di JSONB
    """
    __tablename__ = "messages"
    
    # IDs
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    # CRITICAL message content
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    
    # IMPORTANT links
    sensor_reading_id = Column(Integer, ForeignKey("sensor_readings.reading_id", ondelete="SET NULL"))
    
    # CRITICAL timestamp
    created_at = Column(DateTime, default=func.now())  # Order & session grouping
    
    # JSONB for flexible metadata
    extra_data = Column(JSONType, default=dict)  # {
    #     "session_id": "uuid",  # Group messages into conversations
    #     "intent": "rag/rule_based/hybrid",  # Optional analytics
    #     "confidence": 0.92,  # Optional
    #     "rag_sources": ["doc1.pdf", "doc2.pdf"],  # IMPORTANT: transparency
    #     "rag_images": ["path/to/img1.png"],  # IMPORTANT: multimodal
    #     "processing_time_ms": 450,  # Optional
    #     "conversation_context": {  # Flexible conversation state
    #         "topic": "pH troubleshooting",
    #         "resolved": false
    #     }
    # }
    
    # Relationships
    user = relationship("User", back_populates="messages")
    sensor_reading = relationship("SensorReading", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.message_id}, role={self.role})>"

class SimulatorReading(Base):
    """
    Simulator-specific sensor readings
    Terpisah dari SensorReading untuk membedakan data simulator vs IoT
    """
    __tablename__ = "simulator_readings"
    
    # IDs
    reading_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Sensor values
    ph = Column(Numeric(4, 2), nullable=False)
    tds = Column(Numeric(7, 2), nullable=False)
    temperature = Column(Numeric(4, 2))
    
    # Status
    status = Column(String(20))  # optimal/warning/critical
    source = Column(String(20), default='simulator')  # simulator/iot
    anomaly_injected = Column(Boolean, default=False)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # JSONB for additional metadata
    extra_metadata = Column(JSONType, default=dict)  # {
    #     "drift_applied": {"ph": 0.05, "tds": -10},
    #     "diurnal_factor": 0.8,
    #     "noise_applied": {"ph": 0.02, "tds": 5}
    # }
    
    def __repr__(self):
        return f"<SimulatorReading(id={self.reading_id}, pH={self.ph}, TDS={self.tds}, status={self.status})>"

class UserAction(Base):
    """
    User actions untuk gamification
    Track semua aksi yang dilakukan user (tambah nutrisi, air, dll)
    """
    __tablename__ = "user_actions"
    
    # IDs
    action_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"))
    
    # Action details
    action_type = Column(String(50), nullable=False)  # add_nutrient, add_water, add_ph_down, add_ph_up
    amount = Column(Numeric(5, 2), default=1.0)  # Multiplier untuk effect
    
    # Before/After values
    ph_before = Column(Numeric(4, 2))
    ph_after = Column(Numeric(4, 2))
    tds_before = Column(Numeric(7, 2))
    tds_after = Column(Numeric(7, 2))
    
    # Success tracking
    improved_status = Column(Boolean)  # Apakah action membuat status lebih baik
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # JSONB for additional context
    context = Column(JSONType, default=dict)  # {
    #     "triggered_by": "whatsapp_button",
    #     "alert_id": "uuid",
    #     "recommendation_followed": true
    # }
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserAction(id={self.action_id}, type={self.action_type}, user={self.user_id})>"

class Prediction(Base):
    """
    LLM-based predictions dan recommendations
    Cache hasil prediksi untuk performa
    """
    __tablename__ = "predictions"
    
    # IDs
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Predicted values
    predicted_ph = Column(Numeric(4, 2))
    predicted_tds = Column(Numeric(7, 2))
    prediction_horizon_hours = Column(Integer, default=6)  # Prediksi untuk berapa jam ke depan
    
    # Confidence & recommendation
    confidence = Column(Numeric(3, 2))  # 0.0 - 1.0
    recommendation = Column(Text)  # Natural language recommendation
    recommended_action = Column(String(50))  # Structured action type
    
    # LLM response
    llm_response = Column(Text)  # Full LLM response untuk debugging
    llm_model = Column(String(50))  # Model yang digunakan
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)  # Cache expiration
    
    # JSONB for historical data used
    historical_data = Column(JSONType, default=dict)  # {
    #     "readings_count": 100,
    #     "date_range": {"start": "2025-12-01", "end": "2025-12-08"},
    #     "trends": {"ph": "increasing", "tds": "decreasing"}
    # }
    
    def __repr__(self):
        return f"<Prediction(id={self.prediction_id}, pH={self.predicted_ph}, TDS={self.predicted_tds}, confidence={self.confidence})>"

