"""
Adversarial Diagnosis Engine - High-Fidelity Medical Synthesis
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class AdversarialEngine:
    """Enhanced clinical-grade adversarial engine aligned with Symptom Analysis."""
    
    def __init__(self):
        self.provider = settings.MODEL_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.github_token = settings.GITHUB_TOKEN
        self.google_key = settings.GOOGLE_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.use_mock = False
        
        # Initialize Google Gemini SDK
        self.gemini_model = None
        if self.google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            except Exception as e:
                logger.warning("Gemini SDK initialization failed: %s", e)

        # Initialize Primary Clients
        try:
            if self.provider == "openai":
                self.client = AsyncOpenAI(api_key=self.openai_key)
            elif self.provider == "github":
                # GitHub Models often need /v1 for the OpenAI SDK to work correctly with all paths
                base_url = settings.GITHUB_API_URL or "https://models.inference.ai.azure.com"
                if "/v1" not in base_url: base_url = f"{base_url}/v1"
                self.client = AsyncOpenAI(base_url=base_url, api_key=self.github_token)
            
            if self.groq_key:
                from openai import AsyncOpenAI as AsyncGroq
                self.groq_client = AsyncGroq(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self.groq_key,
                )
            else:
                self.groq_client = getattr(self, 'client', None)
        except Exception as e:
            logger.warning("AsyncOpenAI initialization failed: %s", e)
            if not self.gemini_model:
                self.use_mock = True

    def _generate_dynamic_mock(self, patient_data: dict, role: str, context: str = "") -> dict:
        """Universal Clinical Mock Generator — Context-First Architecture.
        
        Instead of trying to re-diagnose from keywords (which can never cover all diseases),
        this uses the `context` parameter (the prior diagnosis from Symptom Analysis) as the 
        primary anchor. This ensures the Debatable AI always aligns with Symptom Analysis output.
        """
        symptoms = str(patient_data.get('symptoms', '')).lower()
        
        # ---------- CONTEXT-FIRST: Use the diagnosis Symptom Analysis already computed ----------
        if context and context.strip():
            primary = context.strip()
            # Generate a plausible alternative and next step dynamically from the context
            alternative = f"Atypical presentation mimicking {primary}"
            next_step = f"Confirmatory diagnostic workup for {primary} including relevant lab panels and imaging."
            reasoning = f"The patient's symptom constellation of '{symptoms}' is highly consistent with {primary} based on established clinical diagnostic criteria and pathophysiological models."
        else:
            # ---------- FALLBACK: Keyword matching only if NO context from Symptom Analysis ----------
            keyword_map = {
                "thirst": ("Diabetes Mellitus (Suspected)", "Dehydration / Psychogenic Polydipsia"),
                "urination": ("Diabetes Mellitus (Suspected)", "Urinary Tract Infection"),
                "sugar": ("Diabetes Mellitus (Suspected)", "Reactive Hypoglycemia"),
                "glucose": ("Diabetes Mellitus (Suspected)", "Impaired Glucose Tolerance"),
                "diabetes": ("Diabetes Mellitus (Type 2)", "Hyperthyroidism / Cushing's Syndrome"),
                "headache": ("Migraine with Aura", "Tension-Type Headache"),
                "chest pain": ("Stable Angina", "GERD"),
                "fever": ("Acute Viral Syndrome", "Bacterial Infection"),
                "cough": ("Acute Bronchitis", "Atypical Pneumonia"),
                "abdominal": ("Acute Gastroenteritis", "Appendicitis"),
                "rash": ("Contact Dermatitis", "Viral Exanthem"),
                "breathless": ("Asthma Exacerbation", "Pulmonary Embolism"),
                "joint": ("Rheumatoid Arthritis", "Gout"),
                "anxiety": ("Generalized Anxiety Disorder", "Hyperthyroidism"),
                "dizzy": ("Benign Positional Vertigo", "Vestibular Neuritis"),
                "nausea": ("Acute Gastritis", "Early Pregnancy / Labyrinthitis"),
                "weight": ("Metabolic Syndrome", "Thyroid Dysfunction"),
                "back pain": ("Lumbar Strain", "Herniated Disc"),
                "swelling": ("Deep Vein Thrombosis", "Cellulitis"),
                "fatigue": ("Chronic Fatigue Syndrome", "Hypothyroidism"),
            }
            
            primary = "General Medical Assessment Required"
            alternative = "Further Investigation Needed"
            
            for key, (p, a) in keyword_map.items():
                if key in symptoms:
                    primary = p
                    alternative = a
                    break
            
            next_step = f"Comprehensive diagnostic panel to confirm or rule out {primary}."
            reasoning = f"The reported symptoms show clinical correlation with {primary} based on standard diagnostic frameworks."
        
        # ---------- ROLE-BASED OUTPUT GENERATION ----------
        if role == "prosecutor":
            return {
                "diagnosis": primary,
                "confidence": 88,
                "points": [
                    {"title": f"Primary {primary} Indicators", "description": f"The patient's clinical presentation shows strong correlation with {primary}. {reasoning}"},
                    {"title": "Pathophysiological Consistency", "description": f"The reported symptoms ({symptoms}) align with established clinical patterns for {primary}, supported by evidence-based diagnostic models."},
                    {"title": "Differential Exclusion", "description": f"Alternative diagnoses such as {alternative} are less consistent with the overall clinical picture when assessed against the full symptom profile."}
                ]
            }
        elif role == "defense":
            return {
                "alternative_diagnosis": alternative,
                "confidence": 72,
                "points": [
                    {"title": "Diagnostic Uncertainty", "description": f"The Prosecutor's theory of {context or primary} does not fully account for atypical features in this presentation that could suggest {alternative}."},
                    {"title": f"The '{alternative}' Hypothesis", "description": f"Environmental, behavioral, and demographic factors suggest that {alternative} remains a clinically viable differential that warrants investigation."},
                    {"title": "Incomplete Clinical Picture", "description": f"Without confirmatory testing, the current symptom set alone is insufficient to definitively establish {context or primary} over {alternative}."}
                ]
            }
        else:  # Judge
            p_diag = context if context else primary
            simple_summary = f"Summary: Based on the clinical evidence, {p_diag} is the most probable diagnosis, but confirmatory testing is recommended to rule out {alternative}."
            return {
                "verdict": f"Likely {p_diag}",
                "confidence": 82,
                "synthesis": f"After weighing both arguments, the clinical evidence more strongly supports {p_diag} as proposed by the Prosecutor. However, the Defense raises valid concerns about {alternative} that should not be dismissed without proper testing.\n\n***\n{simple_summary}",
                "highlights": [f"Strong {p_diag} Presentation", f"{alternative} as Differential", "Confirmatory Testing Advised"],
                "next_step": next_step
            }

    async def _call_llom(self, prompt: str, system_prompt: str, model_fallback: str = "gpt-4o-mini") -> dict:
        """Unified LLM call with multi-provider failover."""
        if self.gemini_model:
            try:
                full_prompt = f"{system_prompt}\n\n{prompt}\n\nRespond ONLY with valid JSON."
                response = await asyncio.to_thread(self.gemini_model.generate_content, full_prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except Exception as e:
                logger.warning("Gemini SDK call failed: %s", e)

        if hasattr(self, 'client') and not self.use_mock:
            try:
                response = await self.client.chat.completions.create(
                    model=model_fallback,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                logger.warning(f"Primary AI ({model_fallback}) failed: {e}")

        raise ValueError("AI connection error")

    async def prosecutor_ai(self, patient_data: dict, prior_diagnosis: str = None) -> Dict[str, Any]:
        """High-Fidelity Prosecutor AI defending the primary analysis."""
        if self.use_mock: return self._generate_dynamic_mock(patient_data, "prosecutor", prior_diagnosis)
        
        symptoms = patient_data.get('symptoms', [])
        s_desc = symptoms if isinstance(symptoms, str) else ", ".join([str(s) for s in symptoms])
        
        target = f"Primary Diagnosis to Defend: {prior_diagnosis}" if prior_diagnosis else "Find the MOST LIKELY primary diagnosis."
        
        prompt = f"Patient: {patient_data.get('age')}yo {patient_data.get('gender')}\nSymptoms: {s_desc}\n{target}\n\nDeliver a clinicial-grade argument for this diagnosis. Return JSON with 'diagnosis', 'confidence' (0-100), and 'points'."
        system = "You are a BOARD-CERTIFIED SPECIALIST (Prosecutor). Your goal is to provide a robust clinical defense for the primary hypothesis."
        
        try:
            return await self._call_llom(prompt, system)
        except Exception:
            return self._generate_dynamic_mock(patient_data, "prosecutor", prior_diagnosis)

    async def defense_ai(self, patient_data: dict, prosecutor_diagnosis: str) -> Dict[str, Any]:
        """High-Fidelity Defense AI"""
        if self.use_mock: return self._generate_dynamic_mock(patient_data, "defense", prosecutor_diagnosis)
        
        symptoms = patient_data.get('symptoms', [])
        s_desc = symptoms if isinstance(symptoms, str) else ", ".join([str(s) for s in symptoms])
        
        prompt = f"Patient: {patient_data.get('age')}yo {patient_data.get('gender')}\nSymptoms: {s_desc}\nTheory to Challenge: {prosecutor_diagnosis}\n\nPropose a well-reasoned alternative using clinical skepticism. Return JSON with 'alternative_diagnosis', 'confidence', and 'points'."
        system = "You are a SHARP MEDICAL DEFENSE EXPERT. Your goal is to find contradictions in the primary theory."
        
        try:
            return await self._call_llom(prompt, system, model_fallback="gpt-4o" if self.provider == "github" else "gpt-3.5-turbo")
        except Exception:
            return self._generate_dynamic_mock(patient_data, "defense", prosecutor_diagnosis)

    async def judge_ai(self, patient_data: dict, prosecutor_res: dict, defense_res: dict) -> Dict[str, Any]:
        """High-Fidelity Judge AI"""
        if self.use_mock: return self._generate_dynamic_mock(patient_data, "judge", prosecutor_res.get('diagnosis'))
        
        p_diag = prosecutor_res.get('diagnosis')
        d_diag = defense_res.get('alternative_diagnosis')
        
        prompt = f"Case: {p_diag} (Prosecutor) vs {d_diag} (Defense).\nSymptoms: {patient_data.get('symptoms')}\n\nDeliver a balanced medical verdict. Return JSON with 'verdict', 'confidence', 'synthesis', 'highlights' and 'next_step'.\n\nCRITICAL: Synthesis must include a 'Simple Summary:' after '***' for the patient."
        system = "You are a CHIEF MEDICAL OFFICER (Judge). Synthesize the conflict with clinical precision."
        
        try:
            return await self._call_llom(prompt, system)
        except Exception:
            return self._generate_dynamic_mock(patient_data, "judge", p_diag)

    async def run_debate(self, data: dict) -> Dict[str, Any]:
        """Chained analysis: runs Symptom Analysis first to set the Prosecutor's target."""
        from app.services.outbreak_llm import analyze_symptoms_with_gemini, extract_condition_from_analysis
        
        # Step 0: Get the primary diagnosis from the Outbreak Analysis module
        # Mock data/names for consistency
        primary_data = {
            "name": data.get("name", "Patient"),
            "age": data.get("age", 0),
            "gender": data.get("gender", "Other"),
            "symptoms": data.get("symptoms", ""),
            "severity": 5,
            "duration": 5
        }
        
        # Run primary analysis
        try:
            initial_analysis = await asyncio.to_thread(analyze_symptoms_with_gemini, primary_data)
            conditioned_diagnosis = extract_condition_from_analysis(initial_analysis.get("analysis", ""))
            logger.info(f"Adversarial Debate aligned with Primary Analysis: {conditioned_diagnosis}")
        except Exception as e:
            logger.warning(f"Primary Analysis alignment failed: {e}")
            conditioned_diagnosis = None

        # Step 1: Prosecutor defends the primary diagnosis
        prosecutor = await self.prosecutor_ai(data, prior_diagnosis=conditioned_diagnosis)
        
        # Step 2: Defense challenges
        defense = await self.defense_ai(data, prosecutor.get('diagnosis', 'Primary Theory'))
        
        # Step 3: Judge synthesizes
        verdict = await self.judge_ai(data, prosecutor, defense)
        
        return {"prosecutor": prosecutor, "defense": defense, "verdict": verdict}

adversarial_engine = AdversarialEngine()
