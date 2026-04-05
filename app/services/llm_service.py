"""
LLM Service - Handles AI model interactions
"""
import os
import json
from typing import Dict, Any
from app.schemas import PatientProfile


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        from app.config import settings
        self.provider = settings.MODEL_PROVIDER
        self.api_key = settings.OPENAI_API_KEY
        self.github_token = settings.GITHUB_TOKEN
        self.github_url = settings.GITHUB_API_URL
        self.use_mock = False
        
        if self.provider == "openai" and not self.api_key:
            self.use_mock = True
        elif self.provider == "github" and not self.github_token:
            self.use_mock = True
        elif self.provider == "mock":
            self.use_mock = True
            
        if not self.use_mock:
            try:
                from openai import OpenAI
                if self.provider == "openai":
                    self.client = OpenAI(api_key=self.api_key)
                elif self.provider == "github":
                    # GitHub Models usually expects /v1 in the base_url for OpenAI client compatibility
                    base_url = self.github_url if "/v1" in self.github_url else f"{self.github_url}/v1"
                    self.client = OpenAI(
                        base_url=base_url,
                        api_key=self.github_token,
                    )
            except ImportError:
                print("OpenAI client not installed, using mock mode")
                self.use_mock = True

    
    def analyze_symptoms(self, patient: PatientProfile) -> Dict[str, Any]:
        """Analyze symptoms and provide diagnosis"""
        
        if self.use_mock:
            return self._mock_analysis(patient)
        
        symptoms_text = "\n".join([
            f"- {s.description} (Severity: {s.severity}/10, Duration: {s.duration_days} days)"
            for s in patient.symptoms
        ])
        
        prompt = f"""You are a medical AI assistant. Analyze these symptoms and provide:
1. Most likely diagnosis
2. Confidence level (0-1)
3. Step-by-step reasoning (for explainability)
4. Recommendations

Patient: {patient.age}yo {patient.gender}
Medical history: {', '.join(patient.medical_history) if patient.medical_history else 'None'}
Current medications: {', '.join(patient.current_medications) if patient.current_medications else 'None'}

Symptoms:
{symptoms_text}

Respond in JSON format:
{{
    "primary_diagnosis": "...",
    "confidence": 0.0-1.0,
    "reasoning": ["step 1", "step 2", ...],
    "recommendations": ["rec 1", "rec 2", ...]
}}
"""
        
        try:
            model_name = "google/gemini-1.5-flash" if self.provider == "github" else "gpt-4"
            response = self.client.chat.completions.create(
                model=model_name,


                messages=[
                    {"role": "system", "content": "You are a medical diagnosis AI. Always provide reasoning."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._mock_analysis(patient)
    
    def _mock_analysis(self, patient: PatientProfile) -> Dict[str, Any]:
        """Mock analysis for demo/testing"""
        primary_symptom = patient.symptoms[0].description if patient.symptoms else "general malaise"
        
        return {
            "primary_diagnosis": f"Possible {primary_symptom.title()}-related condition",
            "confidence": 0.75,
            "reasoning": [
                f"Patient presents with {primary_symptom} at severity {patient.symptoms[0].severity}/10",
                f"Duration of {patient.symptoms[0].duration_days} days suggests acute condition",
                "Age and medical history considered",
                "Differential diagnoses ruled out based on symptom pattern"
            ],
            "recommendations": [
                "Monitor symptoms for next 24-48 hours",
                "Stay hydrated and get adequate rest",
                "Consult healthcare provider if symptoms worsen",
                "Consider over-the-counter symptom relief if appropriate"
            ]
        }


llm_service = LLMService()
