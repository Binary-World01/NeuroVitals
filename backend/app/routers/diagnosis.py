"""
Diagnosis Router - Standard symptom analysis
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas import PatientProfile, DiagnosisResult
from app.services.llm_service import llm_service

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


@router.post("/analyze", response_model=DiagnosisResult)
async def analyze_symptoms(patient: PatientProfile):
    """Analyze patient symptoms and provide diagnosis"""
    try:
        result = llm_service.analyze_symptoms(patient)
        
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
