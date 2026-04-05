"""
Adversarial Router - Adversarial diagnosis debate
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from schemas import PatientProfile, AdversarialDebateResult
from services.adversarial_engine import adversarial_engine

from services.outbreak_db import save_to_database

router = APIRouter(prefix="/adversarial", tags=["Adversarial"])


@router.post("/debate", response_model=AdversarialDebateResult)
async def run_adversarial_debate(patient: PatientProfile):
    """Run adversarial diagnosis debate"""
    try:
        patient_dict = patient.dict()
        result = adversarial_engine.run_debate(patient_dict)
        
        # --- PERSIST TO DATABASE ---
        # Flatten symptoms if it's a list
        symptoms_str = patient.symptoms
        if isinstance(symptoms_str, list):
            symptoms_str = ", ".join([f"{s.description} (severity {s.severity})" for s in symptoms_str])
        
        db_data = {
            "name": patient.name or "Anonymous",
            "age": patient.age,
            "gender": patient.gender,
            "symptoms": symptoms_str,
            "severity": 0,
            "duration": 0,
            "email": patient.email,
            "form_id": patient.patient_id
        }
        
        # Use the synthesis/verdict as the primary response
        verdict_text = f"Verdict: {result['verdict'].get('verdict')}\n\nSynthesis: {result['verdict'].get('synthesis')}"
        
        save_to_database(
            db_data, 
            ai_response=verdict_text,
            location_data=patient.location_data
        )

        return AdversarialDebateResult(
            prosecutor=result["prosecutor"],
            defense=result["defense"],
            verdict=result["verdict"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")
