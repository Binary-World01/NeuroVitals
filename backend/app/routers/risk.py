"""
Risk Prediction Router — FastAPI endpoints for the risk engine.
Exposes the NeuroFit Risk Prediction Engine via REST API.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.risk_engine import (
    get_or_create_user,
    update_user_profile,
    save_daily_log,
    save_medical_history,
    load_user_history,
    run_risk_prediction,
)
from app.services.ocr_helper import extract_text_from_image

router = APIRouter(prefix="/api/risk", tags=["Risk Engine"])


# ─── Request / Response Models ────────────────────────────────────

class UserProfile(BaseModel):
    email: str = "default@neurovitals.local"
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    existing_conditions: Optional[List[str]] = Field(default_factory=list)
    family_history: Optional[List[str]] = Field(default_factory=list)


class DailyLogInput(BaseModel):
    date: str
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    snacks: Optional[str] = None
    dinner: Optional[str] = None
    water_liters: Optional[float] = 1.5
    exercise_minutes: Optional[int] = 0
    sleep_hours: Optional[float] = 7.0
    symptoms: Optional[str] = None
    steps_today: Optional[int] = 0
    calories_today: Optional[float] = 0.0


class MedicalRecordInput(BaseModel):
    illness_description: str
    illness_date: Optional[str] = None
    prescription_text: Optional[str] = None


class RiskPredictionRequest(BaseModel):
    """Full request for risk prediction — profile + logs + medical records."""
    profile: UserProfile
    daily_log: Optional[DailyLogInput] = None
    medical_records: Optional[List[MedicalRecordInput]] = Field(default_factory=list)


# ─── Endpoints ────────────────────────────────────────────────────

@router.post("/predict")
async def predict_risk(request: RiskPredictionRequest):
    """
    Run full medical risk prediction.
    Accepts user profile, daily log, and medical records.
    Returns AI-generated risk assessment with scores, reasoning, and recommendations.
    """
    try:
        # Get or create user
        user = get_or_create_user(request.profile.email)
        if not user:
            raise HTTPException(status_code=500, detail="Failed to get/create user")

        user_id = user["id"]

        # Update profile if provided
        profile_update = {}
        if request.profile.age:
            profile_update["age"] = request.profile.age
        if request.profile.gender:
            profile_update["gender"] = request.profile.gender
        if request.profile.height_cm:
            profile_update["height_cm"] = request.profile.height_cm
        if request.profile.weight_kg:
            profile_update["weight_kg"] = request.profile.weight_kg
        if request.profile.full_name:
            profile_update["full_name"] = request.profile.full_name
        if request.profile.existing_conditions is not None:
            profile_update["existing_conditions"] = request.profile.existing_conditions
        if request.profile.family_history is not None:
            profile_update["family_history"] = request.profile.family_history

        if profile_update:
            update_user_profile(user_id, profile_update)
            # Refresh user data
            user.update(profile_update)

        # Save daily log if provided
        if request.daily_log:
            save_daily_log(user_id, request.daily_log.model_dump())

        # Save medical records if provided
        if request.medical_records:
            for record in request.medical_records:
                save_medical_history(user_id, record.model_dump())

        # Load full history for AI prompt
        history = load_user_history(user_id)

        # Build user_data dict for prompt
        user_data = {
            "profile": {
                "age": user.get("age", 30),
                "gender": user.get("gender", "other"),
                "height_cm": user.get("height_cm", 170),
                "weight_kg": user.get("weight_kg", 70),
                "existing_conditions": user.get("existing_conditions", []),
                "family_history": user.get("family_history", []),
            },
            "daily_log": request.daily_log.model_dump() if request.daily_log else {},
            "medical_records": [
                {
                    "illness_description": r.get("illness_description", ""),
                    "prescription_text": r.get("prescription_text", ""),
                    "illness_date": r.get("illness_date", ""),
                }
                for r in history.get("medical_history", [])
            ],
            "historical_trends": {
                "daily_logs": history.get("daily_logs", []),
                "recent_predictions": history.get("recent_predictions", []),
            },
        }

        # Run prediction
        result = run_risk_prediction(user_id, user_data)

        return {
            "status": "success",
            "user_id": user_id,
            "prediction": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Risk prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr")
async def extract_prescription_text(file: UploadFile = File(...)):
    """
    Extract text from an uploaded prescription image using OCR.
    Returns the extracted text string.
    """
    try:
        image_bytes = await file.read()
        text = extract_text_from_image(image_bytes)
        return {
            "status": "success",
            "filename": file.filename,
            "extracted_text": text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@router.get("/history/{email}")
async def get_user_history(email: str, days: int = 30):
    """
    Get user's health history (daily logs, medical records, predictions).
    """
    try:
        user = get_or_create_user(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        history = load_user_history(user["id"], days)
        return {
            "status": "success",
            "user_id": user["id"],
            "profile": user,
            "history": history,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-log")
async def save_log(user_email: str, log: DailyLogInput):
    """Save a daily health log entry."""
    try:
        user = get_or_create_user(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        ok, err = save_daily_log(user["id"], log.model_dump())
        if ok:
            return {"status": "success", "message": "Daily log saved"}
        raise HTTPException(status_code=500, detail=err)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medical-record")
async def save_record(user_email: str, record: MedicalRecordInput):
    """Save a medical history record."""
    try:
        user = get_or_create_user(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        ok, err = save_medical_history(user["id"], record.model_dump())
        if ok:
            return {"status": "success", "message": "Medical record saved"}
        raise HTTPException(status_code=500, detail=err)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
