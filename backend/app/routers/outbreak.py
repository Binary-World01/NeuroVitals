"""
Outbreak Router – community health outbreak tracking endpoints.

Exposes:
  POST /api/outbreak/analyze       – symptom analysis with Gemini + save to DB
  GET  /api/outbreak/map           – spreadable diseases for map
  GET  /api/outbreak/map/nearby    – nearby outbreaks by GPS
  GET  /api/outbreak/admin         – all patients (admin dashboard)

Migrated from hackathon_project1/routes.py.
"""

import math
from fastapi import APIRouter, Form, File, UploadFile, Request

from app.services.outbreak_llm import analyze_symptoms_with_gemini
from app.services.outbreak_db import (
    save_to_database,
    upload_file,
    get_spreadable_diseases_for_map,
    get_all_patients_for_admin,
    get_nearby_outbreaks,
    save_admin_report,
)
from app.services.location_service import get_client_location

router = APIRouter(prefix="/outbreak", tags=["outbreak"])


# ──────────────────────────────────────────────
#  Symptom Analysis
# ──────────────────────────────────────────────
@router.post("/analyze")
async def analyze(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    symptoms: str = Form(...),
    severity: int = Form(...),
    duration: int = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    form_id: str = Form(None),
    email: str = Form(None),
    image: UploadFile = File(None),
):
    """Analyse patient symptoms via Gemini, classify, geo-tag, and save."""
    try:
        location_data = await get_client_location(request, latitude, longitude)

        data = {
            "name": name, "age": age, "gender": gender,
            "symptoms": symptoms, "severity": severity, "duration": duration,
            "form_id": form_id, "email": email
        }

        result = analyze_symptoms_with_gemini(data, image_file=image)
        ai_text = result.get("analysis", "")

        img_url = None
        if image and image.filename:
            image.file.seek(0)
            img_url = upload_file(image, "medical_files")

        save_to_database(data, ai_response=ai_text, image_url=img_url, location_data=location_data)

        return {"analysis": ai_text}

    except Exception as exc:
        return {"analysis": f"Error: {exc}"}


@router.post("/broadcast")
async def broadcast_report(
    request: Request,
    symptoms: str = Form(...),
    disease_category: str = Form(...),
    spreadable: bool = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    email: str = Form(None),
):
    """Directly broadcast an outbreak report with geocoding."""
    try:
        location_data = await get_client_location(request, latitude, longitude)
        success = save_admin_report(
            symptoms=symptoms,
            disease_category=disease_category,
            spreadable=spreadable,
            location_data=location_data,
            user_email=email
        )
        return {"success": success}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ──────────────────────────────────────────────
#  Map Endpoints
# ──────────────────────────────────────────────
@router.get("/map")
async def get_spreadable_diseases():
    """Return spreadable diseases for the public outbreak map."""
    diseases = get_spreadable_diseases_for_map()
    return {"diseases": diseases}


@router.get("/map/nearby")
async def get_nearby(lat: float, lng: float, radius: float = 10):
    """Return outbreaks near the user's location."""
    outbreaks = get_nearby_outbreaks(lat, lng, radius)

    for outbreak in outbreaks:
        if outbreak.get("latitude") and outbreak.get("longitude"):
            outbreak["distance_km"] = round(
                _haversine(lat, lng, outbreak["latitude"], outbreak["longitude"]), 1
            )

    return {"nearby": outbreaks, "count": len(outbreaks)}


# ──────────────────────────────────────────────
#  Admin
# ──────────────────────────────────────────────
@router.get("/admin")
async def get_all_patients():
    """Return all patients for the admin dashboard."""
    patients = get_all_patients_for_admin()

    total = len(patients)
    spreadable = sum(1 for p in patients if p.get("spreadable", False))

    return {
        "patients": patients,
        "stats": {
            "total": total,
            "spreadable": spreadable,
            "non_spreadable": total - spreadable,
        },
    }


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371  # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dLon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
