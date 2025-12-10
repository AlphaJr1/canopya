"""
FastAPI Endpoints untuk Onboarding
Handle onboarding flow dan status check

"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from src.core.onboarding_engine import OnboardingEngine
from src.database.base import get_db
from src.database.operations import DatabaseOperations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class OnboardingRequest(BaseModel):
    """Request model untuk onboarding"""
    user_id: str
    message: str

class OnboardingResponse(BaseModel):
    """Response model untuk onboarding"""
    answer: str
    current_step: str
    onboarding_completed: bool

@router.post("", response_model=OnboardingResponse)
async def process_onboarding(request: OnboardingRequest):
    """
    Process onboarding message
    
    Args:
        request: OnboardingRequest dengan user_id dan message
    
    Returns:
        OnboardingResponse dengan answer, current_step, dan completion status
    """
    try:
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        # Get user onboarding status
        onboarding_status = db_ops.get_user_onboarding_status(request.user_id)
        
        # Process message dengan onboarding engine
        engine = OnboardingEngine()
        result = engine.process_message(
            user_data={
                'onboarding_step': onboarding_status['step'],
                'onboarding_data': onboarding_status['data']
            },
            message=request.message
        )
        
        # Merge data_update ke current data untuk next step
        updated_data = onboarding_status['data'].copy()
        updated_data.update(result['data_update'])
        
        # Update database
        if result['completed']:
            # Onboarding completed, save final merged data
            db_ops.complete_onboarding(
                user_id=request.user_id,
                final_data=updated_data
            )
        else:
            # Update progress dengan merged data
            db_ops.update_onboarding_progress(
                user_id=request.user_id,
                step=result['next_step'],
                data_update=updated_data
            )
        
        return OnboardingResponse(
            answer=result['response'],
            current_step=result['next_step'],
            onboarding_completed=result['completed']
        )
    
    except Exception as e:
        logger.error(f"Error in onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{user_id}")
async def get_onboarding_status(user_id: str):
    """
    Get user onboarding status
    
    Args:
        user_id: User ID
    
    Returns:
        Dict dengan completed, step, dan data
    """
    try:
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        status = db_ops.get_user_onboarding_status(user_id)
        
        return status
    
    except Exception as e:
        logger.error(f"Error getting onboarding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset/{user_id}")
async def reset_onboarding(user_id: str):
    """
    Reset onboarding untuk user (untuk testing)
    
    Args:
        user_id: User ID
    
    Returns:
        Success message
    """
    try:
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        db_ops.reset_onboarding(user_id)
        
        return {"message": "Onboarding reset successfully"}
    
    except Exception as e:
        logger.error(f"Error resetting onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))
