"""
Diagnosis Router - Standard symptom analysis
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from schemas import PatientProfile, DiagnosisResult
from services.llm_service import llm_service

from services.outbreak_db import save_to_database

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


@router.post("/analyze", response_model=DiagnosisResult)
async def analyze_symptoms(patient: PatientProfile):
    """Analyze patient symptoms and provide diagnosis"""
    try:
        result = llm_service.analyze_symptoms(patient)
        
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
            "severity": 0, # Default for this schema
            "duration": 0, # Default for this schema
            "email": patient.email,
            "form_id": patient.patient_id
        }
        
        save_to_database(
            db_data, 
            ai_response=result.get("primary_diagnosis", ""),
            location_data=patient.location_data
        )

        return DiagnosisResult(
            primary_diagnosis=result["primary_diagnosis"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            recommendations=result["recommendations"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "diagnosis"}
