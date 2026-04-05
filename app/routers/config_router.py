"""
Config Router — Provide configuration settings to the frontend.
"""
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/config", tags=["Config"])

@router.get("/google-fit")
async def get_google_fit_config():
    """Returns Google Fit Client ID if configured."""
    return {
        "client_id": settings.GOOGLE_FIT_CLIENT_ID,
        "is_configured": settings.GOOGLE_FIT_CLIENT_ID is not None and settings.GOOGLE_FIT_CLIENT_SECRET is not None
    }
