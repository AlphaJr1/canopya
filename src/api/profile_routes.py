from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from src.core.profile_manager import ProfileManager
from src.database.base import get_db
from src.database.operations import DatabaseOperations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile"])

class ProfileViewRequest(BaseModel):
    user_id: str

class ProfileEditRequest(BaseModel):
    user_id: str
    field: str
    new_value: str

class ProfileEditConfirmRequest(BaseModel):
    user_id: str
    update_data: dict

@router.post("/view")
async def view_profile(request: ProfileViewRequest):
    """
    Lihat profil user
    """
    try:
        manager = ProfileManager()
        response = manager.view_profile(request.user_id)
        
        return {
            "response": response,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error viewing profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/edit/start")
async def start_edit(field: str):
    """
    Mulai edit flow untuk field tertentu
    """
    try:
        manager = ProfileManager()
        prompt = manager.start_edit(field)
        
        return {
            "response": prompt,
            "field": field,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error starting edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/edit/process")
async def process_edit(request: ProfileEditRequest):
    """
    Process input baru untuk edit
    """
    try:
        manager = ProfileManager()
        result = manager.process_edit_input(
            user_id=request.user_id,
            field=request.field,
            new_value=request.new_value
        )
        
        if 'error' in result:
            return {
                "response": result['error'],
                "success": False
            }
        
        from src.core.onboarding_messages import get_message
        confirmation = get_message(
            'edit_confirm',
            field=result['field'],
            old_value=result['old_value'],
            new_value=result['new_value']
        )
        
        return {
            "response": confirmation,
            "update_data": result['update_data'],
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error processing edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/edit/confirm")
async def confirm_edit(request: ProfileEditConfirmRequest):
    """
    Konfirmasi dan simpan perubahan
    """
    try:
        manager = ProfileManager()
        response = manager.confirm_edit(
            user_id=request.user_id,
            update_data=request.update_data
        )
        
        return {
            "response": response,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error confirming edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset/{user_id}")
async def reset_profile(user_id: str):
    """
    Reset profil (onboarding ulang)
    """
    try:
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        db_ops.reset_onboarding(user_id)
        
        return {
            "response": "Profil direset. Silakan mulai onboarding dari awal.",
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error resetting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
