"""
Risk Engine Service — Orchestrates the full risk prediction flow.
Combines user data from Supabase with AI prediction via Groq.
Migrated from neurofit_risk_engine14/app.py business logic.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from supabase import create_client, Client
from app.config import settings
from app.services.gemini_helper import call_gemini
from app.services.prompt_builder import build_prompt


def _get_supabase() -> Optional[Client]:
    """Get Supabase client."""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        print("[WARN] Supabase not configured (SUPABASE_URL / SUPABASE_KEY missing)")
        return None
    return create_client(url, key)


def get_or_create_user(email: str = "default@neurovitals.local") -> Optional[dict]:
    """Get existing user by email or create default user."""
    sb = _get_supabase()
    if not sb:
        return None
    try:
        response = sb.table("users").select("*").eq("email", email).limit(1).execute()
        if response.data:
            return response.data[0]
        # Create default user
        insert_response = sb.table("users").insert({
            "email": email, "full_name": "Default User",
            "age": 30, "gender": "other", "height_cm": 170.0, "weight_kg": 70.0,
            "existing_conditions": [], "family_history": []
        }).execute()
        if insert_response.data:
            return insert_response.data[0]
        return None
    except Exception as e:
        print(f"[ERROR] Supabase user error: {e}")
        return None


def update_user_profile(user_id: str, profile_data: dict) -> bool:
    """Update user profile in Supabase."""
    sb = _get_supabase()
    if not sb:
        return False
    try:
        result = sb.table("users").update(profile_data).eq("id", user_id).execute()
        return bool(result.data)
    except Exception as e:
        print(f"[ERROR] Profile update failed: {e}")
        return False


def save_daily_log(user_id: str, log_data: dict) -> tuple:
    """Save or update a daily log entry."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        db_data = {
            "log_date":         log_data["date"],
            "breakfast":        log_data.get("breakfast") or None,
            "lunch":            log_data.get("lunch") or None,
            "snacks":           log_data.get("snacks") or None,
            "dinner":           log_data.get("dinner") or None,
            "water_liters":     log_data.get("water_liters"),
            "exercise_minutes": log_data.get("exercise_minutes"),
            "sleep_hours":      log_data.get("sleep_hours"),
            "symptoms":         log_data.get("symptoms") or None,
            "steps_today":      int(log_data["steps_today"]) if log_data.get("steps_today") else None,
            "calories_today":   float(log_data["calories_today"]) if log_data.get("calories_today") else None,
        }
        existing = sb.table("daily_logs").select("id").eq("user_id", user_id).eq("log_date", log_data["date"]).execute()
        if existing.data:
            result = sb.table("daily_logs").update(db_data).eq("id", existing.data[0]["id"]).execute()
        else:
            db_data["user_id"] = user_id
            result = sb.table("daily_logs").insert(db_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def save_medical_history(user_id: str, history_data: dict) -> tuple:
    """Save a medical history record."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        history_data["user_id"] = user_id
        result = sb.table("medical_history").insert(history_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def load_user_history(user_id: str, days: int = 30) -> dict:
    """Load user's daily logs, medical history, and recent predictions."""
    sb = _get_supabase()
    if not sb:
        return {"daily_logs": [], "medical_history": [], "recent_predictions": []}
    try:
        since = (datetime.now() - timedelta(days=days)).date().isoformat()
        logs = sb.table("daily_logs").select("*").eq("user_id", user_id).gte("log_date", since).order("log_date", desc=True).execute()
        medical = sb.table("medical_history").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        predictions = sb.table("risk_predictions").select("*").eq("user_id", user_id).order("prediction_date", desc=True).limit(10).execute()
        return {
            "daily_logs": logs.data or [],
            "medical_history": medical.data or [],
            "recent_predictions": predictions.data or []
        }
    except Exception as e:
        print(f"[ERROR] Error loading history: {e}")
        return {"daily_logs": [], "medical_history": [], "recent_predictions": []}


def save_risk_prediction(user_id: str, prediction_data: dict) -> tuple:
    """Save a risk prediction result."""
    sb = _get_supabase()
    if not sb:
        return False, "Supabase not configured"
    try:
        prediction_data["user_id"] = user_id
        result = sb.table("risk_predictions").insert(prediction_data).execute()
        if result.data:
            return True, None
        return False, "Supabase returned no data"
    except Exception as e:
        return False, str(e)


def run_risk_prediction(user_id: str, user_data: dict) -> dict:
    """
    Run the full risk prediction pipeline:
    1. Build prompt from user data
    2. Call Groq AI
    3. Save prediction to Supabase
    4. Return result
    """
    # Build prompt
    prompt = build_prompt(user_data)

    # Call AI
    result = call_gemini(prompt)

    # Save to Supabase if successful
    if result.get("risk_level") != "Error":
        prediction_record = {
            "prediction_date": datetime.now().isoformat(),
            "risk_level": result.get("risk_level", "Unknown"),
            "risk_percentages": result.get("risk_percentages", {}),
            "trend_prediction": result.get("trend_prediction", {}),
            "recommendations": result.get("recommendations", []),
            "key_reasons": result.get("key_reasons", []),
        }
        save_risk_prediction(user_id, prediction_record)

    return result
