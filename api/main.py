"""
FastAPI Server untuk Aeropon Hybrid Chatbot
Menyediakan REST API untuk akses chatbot hidroponik/aquaponik

"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.hybrid_chatbot import HybridChatbot
from src.core.rule_engine import SensorReading, GrowthStage
from src.api.onboarding_routes import router as onboarding_router

# Setup logging
import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fastapi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Aeropon Chatbot API",
    description="API untuk chatbot hidroponik/aquaponik dengan RAG Engine dan Rule-Based Diagnostics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ubah sesuai kebutuhan production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot: Optional[HybridChatbot] = None

# Include routers
app.include_router(onboarding_router)

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="Pesan dari user", min_length=1)
    user_id: Optional[str] = Field(default=None, description="User ID untuk personalization")
    language: str = Field(default="id", description="Bahasa response (id/en)")
    include_images: bool = Field(default=True, description="Sertakan gambar dalam response")
    session_id: Optional[str] = Field(default=None, description="Session ID untuk tracking")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Riwayat percakapan untuk konteks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "pH saya 4.5, TDS 1500, bagaimana cara memperbaikinya?",
                "user_id": "628123456789",
                "language": "id",
                "include_images": True,
                "session_id": "user-123",
                "conversation_history": [
                    {"role": "user", "message": "halo"},
                    {"role": "assistant", "message": "Halo! Ada yang bisa saya bantu?"}
                ]
            }
        }

class SensorData(BaseModel):
    """
    """
    ph: Optional[float] = None
    tds: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    growth_stage: Optional[str] = None

class ChatResponse(BaseModel):
    """
    success: bool
    answer: str
    intent: str
    confidence: float
    has_sensor_data: bool
    """
    sensor_data: Optional[Dict[str, Any]] = None
    rag_confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    images: Optional[List[str]] = None
    num_images: int = 0
    pages: Optional[List[int]] = None
    has_visual_support: bool = False
    timestamp: str
    session_id: Optional[str] = None

class HealthResponse(BaseModel):
    """
    status: str
    chatbot_ready: bool
    qdrant_status: str
    ollama_status: str
    timestamp: str

class StatsResponse(BaseModel):
    qdrant_vectors: int
    qdrant_collection: str
    ollama_model: str
    embedding_model: str
    timestamp: str

# Startup event
@app.on_event("startup")
async def startup_event():
    global chatbot
    """
    try:
        chatbot = HybridChatbot()
    except Exception as e:
        logger.error(f"❌ Failed to initialize chatbot: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down Aeropon Chatbot API")

# Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Aeropon Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Mengecek status chatbot, Qdrant, dan Ollama
    """
    try:
        qdrant_status = "healthy"
        ollama_status = "healthy"
        
        if chatbot:
            # Check Qdrant
            try:
                count = chatbot.rag_engine.qdrant.count(
                    collection_name=chatbot.rag_engine.collection_name
                )
                qdrant_status = "healthy"
            except Exception as e:
                logger.error(f"Qdrant health check failed: {e}")
                qdrant_status = "unhealthy"
            
            # Check Ollama
            try:
                import ollama
                ollama.list()
                ollama_status = "healthy"
            except Exception as e:
                logger.error(f"Ollama health check failed: {e}")
                ollama_status = "unhealthy"
        
        return HealthResponse(
            status="healthy" if (chatbot and qdrant_status == "healthy" and ollama_status == "healthy") else "degraded",
            chatbot_ready=chatbot is not None,
            qdrant_status=qdrant_status,
            ollama_status=ollama_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """
    Get system statistics
    Informasi tentang vector database dan model yang digunakan
    """
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot not initialized"
        )
    
    try:
        count = chatbot.rag_engine.qdrant.count(
            collection_name=chatbot.rag_engine.collection_name
        )
        
        return StatsResponse(
            qdrant_vectors=count.count,
            qdrant_collection=chatbot.rag_engine.collection_name,
            ollama_model=chatbot.rag_engine.ollama_model,
            embedding_model="intfloat/multilingual-e5-base",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint - kirim pesan ke chatbot
    
    Chatbot akan otomatis mendeteksi:
    - Data sensor (pH, TDS, suhu, kelembapan)
    - Intent (rule-based, RAG, atau hybrid)
    - Memberikan response yang sesuai dengan konteks
    
    Response bisa berisi:
    - Jawaban text
    - Diagnostik sensor (jika ada data sensor)
    - Gambar/diagram (jika relevan)
    - Sumber referensi
    """
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot not initialized"
        )
    
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        # Process chat
        result = chatbot.chat(
            message=request.message,
            user_id=request.user_id,
            language=request.language,
            include_images=request.include_images,
            conversation_history=request.conversation_history
        )
        
        # Convert sensor_data to dict if present
        sensor_data_dict = None
        if result.get('sensor_data'):
            sd = result['sensor_data']
            sensor_data_dict = {
                'ph': sd.ph,
                'tds': sd.tds,
                'temperature': sd.temperature,
                'humidity': sd.humidity,
                'growth_stage': sd.growth_stage.value if sd.growth_stage else None
            }
        
        # Build response
        response = ChatResponse(
            success=True,
            answer=result['answer'],
            intent=result['intent'],
            confidence=result['confidence'],
            has_sensor_data=result['has_sensor_data'],
            sensor_data=sensor_data_dict,
            rag_confidence=result.get('rag_confidence'),
            sources=result.get('sources'),
            images=result.get('images', []),
            num_images=result.get('num_images', 0),
            pages=result.get('pages'),
            has_visual_support=result.get('has_visual_support', False),
            timestamp=datetime.now().isoformat(),
            session_id=request.session_id
        )
        
        logger.info(f"Chat processed successfully - Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

@app.post("/diagnose", tags=["Diagnostics"])
async def diagnose_sensors(sensor_data: SensorData):
    """
    Endpoint khusus untuk diagnostik sensor
    Langsung memberikan analisis tanpa perlu format chat
    """
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chatbot not initialized"
        )
    
    try:
        # Convert to SensorReading
        from src.core.rule_engine import SensorReading, GrowthStage
        
        reading = SensorReading(
            ph=sensor_data.ph,
            tds=sensor_data.tds,
            temperature=sensor_data.temperature,
            humidity=sensor_data.humidity
        )
        
        # Set growth stage if provided
        if sensor_data.growth_stage:
            stage_map = {
                'seedling': GrowthStage.SEEDLING,
                'vegetative': GrowthStage.VEGETATIVE,
                'fruiting': GrowthStage.FRUITING
            }
            reading.growth_stage = stage_map.get(sensor_data.growth_stage.lower(), GrowthStage.VEGETATIVE)
        
        # Run diagnostics
        result = chatbot.rule_engine.diagnose_all(reading)
        
        return {
            "success": True,
            "summary": result['summary'],
            "diagnostics": result['diagnostics'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Diagnose error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnosis failed: {str(e)}"
        )

@app.get("/user/{user_id}/onboarding-status", tags=["Onboarding"])
async def get_user_onboarding_status(user_id: str):
    """
    Get user onboarding status
    Called by WhatsApp webhook untuk check apakah user perlu onboarding
    """
    try:
        from src.database.base import get_db
        from src.database.operations import DatabaseOperations
        
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        onboarding_status = db_ops.get_user_onboarding_status(user_id)
        
        return onboarding_status
        
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
        )

@app.get("/user/{user_id}", tags=["User"])
async def get_user(user_id: str):
    """Get user profile with plants"""
    try:
        from src.database.base import get_db
        from src.database.operations import DatabaseOperations
        
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        user = db_ops.get_or_create_user(user_id)
        plants = db_ops.get_active_plants(user_id)
        
        return {
            "user_id": user.user_id,
            "name": user.name,
            "onboarding_completed": user.onboarding_completed,
            "last_active": user.last_active.isoformat() if user.last_active else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "plants": [
                {
                    "id": p.plant_id,
                    "name": p.plant_name,
                    "type": p.plant_type,
                    "stage": p.growth_stage,
                    "planting_date": p.planting_date.isoformat() if p.planting_date else None,
                    "is_active": p.is_active
                }
                for p in plants
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {str(e)}"
        )

@app.get("/user/{user_id}/plants", tags=["User"])
async def get_user_plants(user_id: str):
    """Get user's plants"""
    try:
        from src.database.base import get_db
        from src.database.operations import DatabaseOperations
        
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        plants = db_ops.get_active_plants(user_id)
        
        return {
            "user_id": user_id,
            "plants": [
                {
                    "id": p.plant_id,
                    "name": p.plant_name,
                    "type": p.plant_type,
                    "stage": p.growth_stage,
                    "planting_date": p.planting_date.isoformat() if p.planting_date else None,
                    "is_active": p.is_active
                }
                for p in plants
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting user plants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plants: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
