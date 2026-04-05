from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
import json
import os
import uuid
from datetime import datetime
from app.schemas import Medication, MedicationCreate
from app.services.outbreak_llm import scan_prescription

router = APIRouter(prefix="/medications", tags=["Medication"])

# Local storage path
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "medications_db.json")

def _load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def _save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/{user_email}", response_model=List[Medication])
async def get_medications(user_email: str):
    """List all medications from local JSON store."""
    db = _load_db()
    user_meds = [m for m in db if m.get("user_email") == user_email]
    return user_meds

@router.post("/", response_model=Medication)
async def add_medication(med: MedicationCreate, user_email: str):
    """Add a new medication to local JSON store."""
    db = _load_db()
    new_med = med.model_dump()
    new_med["id"] = str(uuid.uuid4())
    new_med["user_email"] = user_email
    new_med["created_at"] = datetime.now().isoformat()
    
    db.append(new_med)
    _save_db(db)
    return new_med

@router.delete("/{med_id}")
async def delete_medication(med_id: str):
    """Delete a medication from local JSON store."""
    db = _load_db()
    new_db = [m for m in db if m.get("id") != med_id]
    if len(new_db) == len(db):
        raise HTTPException(status_code=404, detail="Medication not found.")
    _save_db(new_db)
    return {"status": "success", "message": "Medication deleted"}

@router.post("/scan")
async def scan_medication_prescription(file: UploadFile = File(...)):
    """AI OCR: Extract medication info from prescription image."""
    try:
        data = scan_prescription(file)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
