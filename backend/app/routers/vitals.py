"""
Vitals Router — Save and retrieve vitals data from Google Fit to Supabase.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

router = APIRouter(prefix="/vitals", tags=["Vitals"])

from app.config import settings

# Supabase client
try:
    from supabase import create_client
    SUPABASE_URL = settings.SUPABASE_URL
    SUPABASE_KEY = settings.SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except Exception:
    supabase = None

class VitalsData(BaseModel):
    user_email: str
    steps: Optional[int] = 0
    heart_rate: Optional[int] = 0
    sleep_hours: Optional[float] = 0.0
    calories: Optional[int] = 0
    source: Optional[str] = "google_fit"
    recorded_at: Optional[datetime] = None

@router.get("/health")
async def vitals_health():
    return {"status": "ok", "supabase": supabase is not None}

@router.post("/save-vitals")
async def save_vitals(vitals: VitalsData):
    """Save vitals data from Google Fit to Supabase (upsert)"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        print(f"Received vitals data for: {vitals.user_email}")
        
        # Prepare data for Supabase
        data = {
            "user_email": vitals.user_email,
            "steps": vitals.steps or 0,
            "heart_rate": vitals.heart_rate or 0,
            "sleep_hours": float(vitals.sleep_hours or 0),
            "calories": vitals.calories or 0,
            "source": vitals.source,
            "recorded_at": (vitals.recorded_at or datetime.now()).isoformat()
        }
        
        # ATOMIC UPSERT: Single row per user_email
        # We use on_conflict='user_email' to ensure we update the existing row
        try:
            result = supabase.table("user_vitals").upsert(data, on_conflict="user_email").execute()
            print(f"SUCCESS: [Supabase] Data synced successfully for {vitals.user_email}")
            
            return {
                "status": "success", 
                "message": "Vitals synchronized to Supabase",
                "data": result.data
            }
        except Exception as inner_e:
            error_str = str(inner_e)
            if "23503" in error_str or "foreign key" in error_str.lower():
                print(f"WARNING: [Supabase] Foreign key violation for {vitals.user_email}. User not in medical_forms.")
                raise HTTPException(
                    status_code=400, 
                    detail="User profile not complete. Please fill the medical assessment form first."
                )
            raise inner_e
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: [Supabase] Details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-vitals/{user_email}")
async def get_vitals(user_email: str):
    """Retrieve all vitals for a specific user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = supabase.table("user_vitals").select("*").eq("user_email", user_email).execute()
        return {"status": "success", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-latest-vitals/{user_email}")
async def get_latest_vitals(user_email: str):
    """Retrieve the single record for a specific user (same as get-vitals if one-row-per-user)"""
    return await get_vitals(user_email)

@router.delete("/delete-vitals/{user_email}")
async def delete_vitals(user_email: str):
    """Delete vitals for a specific user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = supabase.table("user_vitals").delete().eq("user_email", user_email).execute()
        return {"status": "success", "message": f"Deleted vitals for {user_email}", "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
