import requests
from fastapi import APIRouter, HTTPException, Form
from app.config import settings
from typing import Dict

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/app-config")
async def get_app_config() -> Dict[str, str]:
    """Expose only non-sensitive config needed for frontend apps"""
    return {
        "google_fit_client_id": settings.GOOGLE_FIT_CLIENT_ID or "",
        "supabase_url": settings.SUPABASE_URL or "",
        "supabase_anon_key": settings.SUPABASE_KEY or ""
    }

@router.get("/google-fit")
async def get_google_fit_config() -> Dict[str, str]:
    """Expose only non-sensitive config needed for frontend OAuth"""
    return {
        "client_id": settings.GOOGLE_FIT_CLIENT_ID or ""
    }

@router.post("/google-fit/exchange")
async def exchange_token(code: str = Form(...), redirect_uri: str = Form(...)):
    """Proxy token exchange to Google to keep CLIENT_SECRET on backend"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_FIT_CLIENT_ID,
        "client_secret": settings.GOOGLE_FIT_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    resp = requests.post(url, data=data)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.post("/google-fit/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    """Proxy token refresh to Google to keep CLIENT_SECRET on backend"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GOOGLE_FIT_CLIENT_ID,
        "client_secret": settings.GOOGLE_FIT_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    resp = requests.post(url, data=data)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
