"""
Vitals Router — Save and retrieve vitals data from Google Fit to Supabase.
(Reverted to March 22nd Sunday Version)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.config import settings

router = APIRouter(prefix="/vitals", tags=["Vitals"])

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
        
        # UPSERT: Update if user_email exists, insert if not
        # The 'on_conflict' parameter ensures we target the unique user_email field
        try:
            result = supabase.table("user_vitals")\
                .upsert(data, on_conflict="user_email")\
                .execute()
            
            print(f"SUCCESS: [Supabase] Data saved/updated for {vitals.user_email}")
            
            return {
                "status": "success", 
                "message": "Vitals saved to Supabase",
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
