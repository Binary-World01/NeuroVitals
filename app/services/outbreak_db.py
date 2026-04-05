"""
Outbreak Database Service – Supabase CRUD for patient records,
admin outbreak tracking, and map queries.

Migrated from hackathon_project1/supabase_service.py.
Uses the same Supabase instance as the rest of the app.
"""

import uuid
import math
import logging
from datetime import datetime, timedelta

from supabase import create_client, Client
from app.config import settings
from app.services.disease_classifier import DiseaseClassifier

logger = logging.getLogger(__name__)

# Initialise Supabase client
_supabase: Client | None = None


def _get_sb() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase


# ──────────────────────────────────────────────
#  Housekeeping
# ──────────────────────────────────────────────
def cleanup_old_records():
    """Delete admin records older than 20 days."""
    try:
        cutoff = (datetime.now() - timedelta(days=20)).isoformat()
        result = _get_sb().table("admin").delete().lt("created_at", cutoff).execute()
        if result.data:
            logger.info("Cleaned up %d old outbreak records", len(result.data))
    except Exception as exc:
        logger.error("Cleanup error: %s", exc)


# ──────────────────────────────────────────────
#  File upload
# ──────────────────────────────────────────────
def upload_file(file, bucket_name: str = "medical_files") -> str | None:
    try:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_content = file.file.read()

        _get_sb().storage.from_(bucket_name).upload(
            path=unique_name,
            file=file_content,
            file_options={"content-type": file.content_type},
        )
        return str(_get_sb().storage.from_(bucket_name).get_public_url(unique_name))
    except Exception as exc:
        logger.error("Upload error: %s", exc)
        return None


# ──────────────────────────────────────────────
#  Save patient + admin record
# ──────────────────────────────────────────────
def save_to_database(
    data: dict,
    ai_response: str | None = None,
    image_url: str | None = None,
    location_data: dict | None = None,
) -> int | None:
    try:
        disease_info = DiseaseClassifier.classify_disease(ai_response)
        form_id = data.get("form_id")

        patient_record = {
            "name": data["name"],
            "age": data["age"],
            "gender": data["gender"],
            "symptoms": data["symptoms"],
            "severity": data["severity"],
            "duration": data["duration"],
            "ai_response": ai_response,
            "image_url": image_url,
            "created_at": datetime.now().isoformat(),
        }

        # Use upsert if form_id is provided, otherwise insert
        if form_id:
            patient_record["form_id"] = form_id
            result = _get_sb().table("records").upsert(patient_record, on_conflict="form_id").execute()
        else:
            result = _get_sb().table("records").insert(patient_record).execute()

        if result.data:
            patient_id = result.data[0]["id"]

            if location_data and location_data.get("latitude"):
                admin_record = {
                    "patient_id": patient_id,
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude"),
                    "location_city": location_data.get("city"),
                    "location_region": location_data.get("region"),
                    "location_country": location_data.get("country"),
                    "disease_category": disease_info["category"],
                    "spreadable": disease_info["spreadable"],
                    "disease_type": disease_info["disease_type"],
                    "created_at": datetime.now().isoformat(),
                }
                # Upsert admin record on patient_id to prevent duplicates for the same case
                _get_sb().table("admin").upsert(admin_record, on_conflict="patient_id").execute()

            logger.info("Saved/Updated patient %s (disease: %s)", patient_id, disease_info["disease_type"])
            return patient_id

    except Exception as exc:
        logger.error("Database save error: %s", exc)
    return None


# ──────────────────────────────────────────────
#  Map queries
# ──────────────────────────────────────────────
def get_spreadable_diseases_for_map() -> list:
    """Return spreadable-only diseases from the last 20 days."""
    try:
        cleanup_old_records()
        cutoff = (datetime.now() - timedelta(days=20)).isoformat()

        result = (
            _get_sb()
            .table("admin")
            .select(
                "id, latitude, longitude, location_city, location_region, "
                "disease_category, disease_type, created_at, "
                "records:patient_id (name, age, gender, symptoms, severity)"
            )
            .eq("spreadable", True)
            .gte("created_at", cutoff)
            .not_.is_("latitude", "null")
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Map query error: %s", exc)
        return []


def get_all_patients_for_admin() -> list:
    """Return every patient record for the admin dashboard."""
    try:
        cleanup_old_records()
        result = (
            _get_sb()
            .table("admin")
            .select("*, records:patient_id (*)")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Admin query error: %s", exc)
        return []


def get_nearby_outbreaks(user_lat: float, user_lng: float, radius_km: float = 10) -> list:
    """Return spreadable outbreaks within a bounding box around the user."""
    try:
        lat_diff = radius_km / 111.0
        lng_diff = radius_km / (111.0 * abs(math.cos(math.radians(user_lat))))

        result = (
            _get_sb()
            .table("admin")
            .select("*, records:patient_id (name, symptoms, severity)")
            .eq("spreadable", True)
            .gte("latitude", user_lat - lat_diff)
            .lte("latitude", user_lat + lat_diff)
            .gte("longitude", user_lng - lng_diff)
            .lte("longitude", user_lng + lng_diff)
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.error("Nearby query error: %s", exc)
        return []
