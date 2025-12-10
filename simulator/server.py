"""
FastAPI Server untuk Simulator pH & TDS
REST API untuk integrasi dengan chatbot dan IoT

"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from data_generator import NFTDataGenerator
from database_integration import SimulatorDatabase
from gamification import GamificationEngine
from lstm_predictor import LLMPredictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Global instances
generator = None
db = None
gamification = None
predictor = None
server_start_time = None

# Pydantic models untuk request/response
class ActionRequest(BaseModel):
    action_type: str = Field(..., description="Tipe action: add_nutrient, add_water, add_ph_down, add_ph_up")
    amount: float = Field(default=1.0, ge=0.1, le=3.0, description="Multiplier untuk effect (0.1 - 3.0)")
    user_id: Optional[str] = Field(default=None, description="User ID (opsional)")

class ActionResponse(BaseModel):
    """Response model untuk action endpoint"""
    success: bool
    message: str
    before: Dict
    after: Dict
    improved: bool

class CurrentResponse(BaseModel):
    """Response model untuk current endpoint"""
    timestamp: str
    ph: float
    tds: float
    temperature: Optional[float]
    status: str
    anomaly_injected: bool
    source: str

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int
    database_connected: bool
    ollama_available: bool
    total_readings: int

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global generator, db, gamification, predictor, server_start_time
    
    # Startup
    server_start_time = datetime.now()
    
    try:
        generator = NFTDataGenerator()
        db = SimulatorDatabase()
        gamification = GamificationEngine()
        predictor = LLMPredictor()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down simulator server...")
    
    # Save current state
    try:
        current_state = generator.get_current_state()
        with open('data/current_state.json', 'w') as f:
            json.dump(current_state, f, indent=2)
        logger.info("State saved")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

# Create FastAPI app
app = FastAPI(
    title="Aeropon Simulator API",
    description="REST API untuk simulator pH & TDS sistem hidroponik NFT",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
async def root():
    return {
        "message": "Aeropon Simulator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/current", response_model=CurrentResponse, tags=["Sensor Data"])
async def get_current():
    """
    Get current sensor values
    Returns nilai pH, TDS, temperature, dan status terkini
    """
    try:
        state = generator.get_current_state()
        return CurrentResponse(**state)
    except Exception as e:
        logger.error(f"Error getting current state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", tags=["Sensor Data"])
async def get_history(
    hours: int = 24,
    insights: bool = False
):
    """
    Get historical sensor data
    
    Args:
        hours: Berapa jam ke belakang (default: 24)
        insights: Include insights analysis (default: False)
    
    Returns:
        List of readings dan optional insights
    """
    try:
        readings = db.get_readings_since(hours=hours)
        
        result = {
            'period_hours': hours,
            'total_readings': len(readings),
            'readings': [
                {
                    'timestamp': r.created_at.isoformat(),
                    'ph': float(r.ph),
                    'tds': float(r.tds),
                    'temperature': float(r.temperature) if r.temperature else None,
                    'status': r.status,
                    'anomaly_injected': r.anomaly_injected
                }
                for r in readings
            ]
        }
        
        if insights:
            result['insights'] = db.get_insights(hours=hours)
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/action", response_model=ActionResponse, tags=["Gamification"])
async def perform_action(action: ActionRequest):
    """
    Perform user action (gamification)
    
    Args:
        action: ActionRequest dengan action_type dan amount
    
    Returns:
        ActionResponse dengan before/after values dan status
    """
    try:
        # Get current state
        current_state = generator.get_current_state()
        
        # Validate action
        validation = gamification.validate_action(action.action_type, current_state)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['reason'])
        
        # Record before values
        before = {
            'ph': current_state['ph'],
            'tds': current_state['tds'],
            'status': current_state['status']
        }
        
        # Apply action
        result = generator.apply_user_action(action.action_type, action.amount)
        
        # Get after state
        after_state = generator.get_current_state()
        after = {
            'ph': after_state['ph'],
            'tds': after_state['tds'],
            'status': after_state['status']
        }
        
        # Check improvement
        improved = gamification.check_improvement(before['status'], after['status'])
        
        # Save action to database
        action_data = {
            'user_id': action.user_id,
            'action_type': action.action_type,
            'amount': action.amount,
            'ph_before': before['ph'],
            'ph_after': after['ph'],
            'tds_before': before['tds'],
            'tds_after': after['tds'],
            'improved_status': improved,
            'context': {
                'triggered_by': 'api',
                'timestamp': datetime.now().isoformat()
            }
        }
        db.save_action(action_data)
        
        # Clear prediction cache (karena state berubah)
        predictor.clear_cache()
        
        return ActionResponse(
            success=True,
            message=f"Action {action.action_type} berhasil dilakukan",
            before=before,
            after=after,
            improved=improved
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict", tags=["Prediction"])
async def get_prediction(force_refresh: bool = False):
    """
    Get LLM-based prediction dan recommendation
    
    Args:
        force_refresh: Force refresh cache (default: False)
    
    Returns:
        Prediction dengan trend analysis dan rekomendasi
    """
    try:
        # Get historical data
        historical_readings = db.get_readings_since(hours=168)  # 7 hari
        
        if not historical_readings:
            raise HTTPException(
                status_code=404,
                detail="Tidak ada data historis untuk prediksi"
            )
        
        # Get latest reading
        latest = generator.get_current_state()
        
        # Get prediction
        prediction = predictor.predict(
            historical_readings,
            latest,
            force_refresh=force_refresh
        )
        
        if not prediction:
            raise HTTPException(
                status_code=500,
                detail="Gagal generate prediksi. Pastikan Ollama running."
            )
        
        # Save prediction to database
        prediction_data = prediction.copy()
        prediction_data['expires_at'] = datetime.now() + timedelta(
            minutes=config['llm']['cache_duration_minutes']
        )
        db.save_prediction(prediction_data)
        
        return prediction
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights", tags=["Analysis"])
async def get_insights(hours: int = 24):
    """
    Get automated insights dan alerts
    
    Args:
        hours: Berapa jam ke belakang untuk analisis (default: 24)
    
    Returns:
        Insights dengan trends, anomalies, dan alerts
    """
    try:
        insights = db.get_insights(hours=hours)
        return insights
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint
    Returns status server, database, dan Ollama
    """
    try:
        # Check database
        db_connected = True
        try:
            db.get_readings_count()
        except:
            db_connected = False
        
        # Check Ollama
        ollama_available = predictor._check_ollama_health()
        
        # Calculate uptime
        uptime = (datetime.now() - server_start_time).total_seconds()
        
        # Get total readings
        total_readings = db.get_readings_count() if db_connected else 0
        
        status = "healthy" if (db_connected and ollama_available) else "degraded"
        
        return HealthResponse(
            status=status,
            uptime_seconds=int(uptime),
            database_connected=db_connected,
            ollama_available=ollama_available,
            total_readings=total_readings
        )
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Analysis"])
async def get_stats():
    """
    Get statistics tentang simulator
    Returns stats tentang readings, actions, dan achievements
    """
    try:
        # Get action stats
        action_stats = db.get_action_stats()
        
        # Get reading stats
        total_readings = db.get_readings_count()
        recent_readings = db.get_readings_since(hours=24)
        
        # Calculate uptime
        uptime = (datetime.now() - server_start_time).total_seconds()
        
        return {
            'uptime_seconds': int(uptime),
            'total_readings': total_readings,
            'readings_last_24h': len(recent_readings),
            'action_stats': action_stats,
            'server_start_time': server_start_time.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate", tags=["Development"])
async def generate_reading(background_tasks: BackgroundTasks):
    """
    Manually trigger reading generation (untuk testing)
    Returns generated reading
    """
    try:
        reading = generator.generate_next_reading()
        
        # Save to database in background
        background_tasks.add_task(db.save_reading, reading)
        
        # Save to current_state.json
        with open('data/current_state.json', 'w') as f:
            json.dump(reading, f, indent=2)
        
        return reading
    
    except Exception as e:
        logger.error(f"Error generating reading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run server
    server_config = config['server']
    
    uvicorn.run(
        "server:app",
        host=server_config['host'],
        port=server_config['port'],
        reload=server_config['reload'],
        log_level="info"
    )
