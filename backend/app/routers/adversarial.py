"""
Adversarial Router - Adversarial diagnosis debate
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas import PatientProfile, AdversarialDebateResult
from app.services.adversarial_engine import adversarial_engine

router = APIRouter(prefix="/adversarial", tags=["Adversarial"])


@router.post("/debate", response_model=AdversarialDebateResult)
async def run_adversarial_debate(patient: PatientProfile):
    """Run adversarial diagnosis debate"""
    try:
        patient_dict = patient.dict()
        result = adversarial_engine.run_debate(patient_dict)
        
        return AdversarialDebateResult(
            prosecutor=result["prosecutor"],
            defense=result["defense"],
            verdict=result["verdict"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate failed: {str(e)}")
