"""
Pydantic schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum


class SymptomInput(BaseModel):
    """Individual symptom entry"""
    description: str = Field(..., description="Symptom description")
    severity: int = Field(..., ge=1, le=10, description="Severity 1-10")
    duration_days: int = Field(..., ge=0, description="How long has this lasted")
    onset_time: Optional[str] = Field(None, description="morning/afternoon/evening/night")


class PatientProfile(BaseModel):
    """Complete patient profile"""
    patient_id: str
    age: int
    gender: str
    symptoms: Union[List[SymptomInput], str]
    medical_history: Optional[List[str]] = Field(default_factory=list)
    current_medications: Optional[List[str]] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    """Standard diagnosis result"""
    primary_diagnosis: str
    confidence: float = Field(..., ge=0, le=1)
    reasoning: List[str]
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AdversarialDebateResult(BaseModel):
    """Result from adversarial diagnosis engine"""
    prosecutor: dict
    defense: dict
    verdict: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrajectoryForecast(BaseModel):
    """Health trajectory forecast"""
    current_risk: float
    baseline_projection: dict
    intervention_projection: dict
    diagnosis: str
    key_interventions: List[str]


class CommunityHealthData(BaseModel):
    """Community health intelligence"""
    total_reports: int
    recent_24h: int
    transmission_velocity: float
    trending_symptoms: List[tuple]
    area_data: List[dict]
    map_points: List[dict]


class MedicationBase(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    time_of_day: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True


class MedicationCreate(MedicationBase):
    pass


class Medication(MedicationBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
