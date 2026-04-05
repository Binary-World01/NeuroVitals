"""
Trajectory Router - Health trajectory forecasting
"""
from fastapi import APIRouter, HTTPException
from app.schemas import PatientProfile, TrajectoryForecast
from app.services.trajectory_service import trajectory_service

router = APIRouter(prefix="/trajectory", tags=["Trajectory"])


@router.post("/forecast", response_model=TrajectoryForecast)
async def forecast_trajectory(patient: PatientProfile, diagnosis: str = "General Health Risk"):
    """Calculate 6-month health trajectory forecast"""
    try:
        result = trajectory_service.calculate_trajectory(patient, diagnosis)
        return TrajectoryForecast(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")
