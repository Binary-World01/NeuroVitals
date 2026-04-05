"""
Temporal Health Trajectory - 6-month forecasting
"""
from typing import Dict, Any
from app.schemas import PatientProfile


class TrajectoryService:
    """Health trajectory forecasting"""
    
    def calculate_trajectory(self, patient: PatientProfile, diagnosis: str) -> Dict[str, Any]:
        """Calculate 6-month health trajectory"""
        
        # Base risk calculation
        base_risk = 0.3
        
        # Risk factors
        age_factor = max(0, (patient.age - 30) * 0.01)
        severity_factor = sum([s.severity for s in patient.symptoms]) * 0.02
        history_factor = len(patient.medical_history) * 0.05
        
        current_risk = min(base_risk + age_factor + severity_factor + history_factor, 0.95)
        
        # Baseline projection (no intervention)
        baseline_projection = {
            "month_1": min(current_risk + 0.05, 0.98),
            "month_2": min(current_risk + 0.10, 0.98),
            "month_3": min(current_risk + 0.18, 0.98),
            "month_4": min(current_risk + 0.28, 0.98),
            "month_5": min(current_risk + 0.40, 0.98),
            "month_6": min(current_risk + 0.55, 0.98)
        }
        
        # With intervention projection
        intervention_projection = {
            "month_1": max(current_risk - 0.02, 0.05),
            "month_2": max(current_risk - 0.08, 0.05),
            "month_3": max(current_risk - 0.15, 0.05),
            "month_4": max(current_risk - 0.22, 0.05),
            "month_5": max(current_risk - 0.30, 0.05),
            "month_6": max(current_risk - 0.40, 0.05)
        }
        
        return {
            "current_risk": round(current_risk, 2),
            "baseline_projection": baseline_projection,
            "intervention_projection": intervention_projection,
            "diagnosis": diagnosis,
            "key_interventions": [
                "Lifestyle modification (diet and exercise)",
                "Medication adherence as prescribed",
                "Regular health monitoring and check-ups",
                "Stress management techniques",
                "Sleep hygiene improvement"
            ],
            "risk_reduction": round((current_risk - intervention_projection["month_6"]) * 100, 1)
        }


trajectory_service = TrajectoryService()
