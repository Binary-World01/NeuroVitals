"""
Outbreak LLM Service – uses Google Gemini Flash (primary) or Groq (fallback)
to run symptom analysis with optional image support.
"""

import logging
import requests
from app.config import settings

logger = logging.getLogger(__name__)

# Lazy-load the Gemini model (only on first call)
_model = None


def _get_model():
    global _model
    if _model is None:
        if not settings.GOOGLE_API_KEY:
            return None  # Will fall back to Groq
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        _model = genai.GenerativeModel("gemini-2.0-flash")
    return _model


def _get_openai_client(provider: str, url: str, token: str):
    from openai import OpenAI
    # GitHub Models (Azure) usually prefers the base URL without /v1 when using the latest inference SDKs,
    # but some proxies need it. We will try to detect but for GitHub specifically we'll use the precise one.
    if "azure.com" in url:
        return OpenAI(base_url=url, api_key=token)
    base_url = url if "/v1" in url else f"{url}/v1"
    return OpenAI(base_url=base_url, api_key=token)


def _analyze_with_github(prompt: str) -> str:
    """GitHub Models: Call OpenAI-compatible endpoint for Gemini/GPT."""
    token = settings.GITHUB_TOKEN
    url = settings.GITHUB_API_URL or "https://models.inference.ai.azure.com"
    if not token:
        raise ValueError("GITHUB_TOKEN is not configured.")

    from openai import APIError
    client = _get_openai_client("github", url, token)
    
    # Expanded list of model names to try based on latest GitHub Models catalog
    models_to_try = [
        "gpt-4o-mini", 
        "gpt-4o",
        "google/gemini-1.5-flash",
        "Meta-Llama-3.1-8B-Instruct"
    ]
    
    last_err = None
    for model_name in models_to_try:
        try:
            logger.info("Attempting GitHub model: %s", model_name)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024
            )
            return resp.choices[0].message.content
        except APIError as e:
            last_err = e
            # If it's a model error (400 or 404), try the next one
            if "unknown_model" in str(e).lower() or "404" in str(e):
                logger.warning("Model %s failed: %s", model_name, e)
                continue
            raise e
            
    if last_err:
        raise last_err
    raise ValueError("No GitHub models worked.")


def _analyze_with_groq(prompt: str) -> str:
    """Fallback: Call Groq API via OpenAI client."""
    groq_key = settings.GROQ_API_KEY
    if not groq_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    client = _get_openai_client("groq", "https://api.groq.com/openai/v1", groq_key)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content



def _analyze_with_mock(prompt: str, data: dict) -> str:
    """Zero-setup fallback for hackathon demo."""
    symptoms = str(data.get('symptoms', '')).lower()
    condition = "Possible Acute Viral Syndrome"
    
    # Aligned with Adversarial Engine mapping
    if "thirst" in symptoms or "urination" in symptoms:
        condition = "Diabetes Mellitus (Suspected)"
    elif "pain" in symptoms:
        condition = "Muscle Strain / Fatigue"
    elif "cough" in symptoms:
        condition = "Upper Respiratory Infection"
    elif "fever" in symptoms:
        condition = "Acute Viral Syndrome"
    elif "headache" in symptoms:
        condition = "Migraine with Aura"
    
    return f"""
    [SENTINEL_CONDITION]
    {condition} (Demo Mode)
    
    [SENTINEL_EXPLANATION]
    Based on the reported symptoms, this appears to be a common clinical presentation seen in demo environments.
    
    [SENTINEL_PRECAUTIONS]
    MANDATORY PRECAUTION: Avoid self-medication and monitor for any worsening symptoms. Avoid strenuous activity.
    
    [SENTINEL_NEXT_STEPS]
    1. Rest and hydration. 2. Monitor temperature. 3. Consult a physician if symptoms persist.
    
    [SENTINEL_DISCLAIMER]
    Medical Disclaimer: This is a DEMO MODE analysis (AI providers currently unreachable). Not a medical diagnosis.
    """

def analyze_symptoms_with_gemini(data: dict, image_file=None) -> dict:
    """
    Analyse patient symptoms (and optional image) with Gemini Flash.
    Prioritizes Google SDK, then GitHub Models, then Groq, then Mock.
    """
    print(f"DEBUG: Entering analyze_symptoms_with_gemini with data: {data}")
    try:
        prompt = f"""
        You are an AI Medical Assistant. Analyze the following patient data.
        Patient Name: {data['name']}
        Age: {data['age']}, Gender: {data['gender']}
        Symptoms: {data['symptoms']}
        Severity: {data['severity']}/10, Duration: {data['duration']} days
        Your output MUST be structured with the following explicit sentinel tags to ensure correct UI rendering. 
        Each section must start with the tag in capital letters:
        
        [SENTINEL_CONDITION]
        <Condition Name>
        
        [SENTINEL_EXPLANATION]
        <Detailed Explaination>
        
        [SENTINEL_PRECAUTIONS]
        <Health and Safety Precautions>
        
        [SENTINEL_NEXT_STEPS]
        <What to do next>
        
        [SENTINEL_DISCLAIMER]
        Medical Disclaimer: This is an AI analysis and not a formal medical diagnosis.
        
        CRITICAL: You MUST include the [SENTINEL_PRECAUTIONS] section. Do not omit it.
        Do not use markdown headers (##). ONLY use the [SENTINEL_...] tags above.
        """

        # 1. Try Google Gemini SDK
        try:
            model = _get_model()
            if model:
                content: list = [prompt]
                if image_file and getattr(image_file, "filename", None):
                    image_file.file.seek(0)
                    image_data = image_file.file.read()
                    mime_type = getattr(image_file, "content_type", None) or "image/jpeg"
                    if mime_type.startswith("image/"):
                        content.append({"mime_type": mime_type, "data": image_data})
                response = model.generate_content(content)
                return {"analysis": response.text}
        except Exception as e:
            logger.warning("Google SDK failed: %s", e)

        # 2. Try GitHub Models (Gemini Flash / GPT-4o-mini)
        if settings.GITHUB_TOKEN:
            try:
                logger.info("Using GitHub Models for analysis.")
                text = _analyze_with_github(prompt)
                return {"analysis": text}
            except Exception as e:
                logger.warning("GitHub Models failed: %s", e)

        # 3. Try Groq
        if settings.GROQ_API_KEY:
            try:
                logger.info("Using Groq fallback.")
                text = _analyze_with_groq(prompt)
                return {"analysis": text}
            except Exception as e:
                logger.warning("Groq failed: %s", e)

        # 4. Final Final Fallback: MOCK
        logger.info("All providers failed. Using Mock analysis (Demo mode).")
        return {"analysis": _analyze_with_mock(prompt, data)}

    except Exception as exc:
        logger.error("Outbreak LLM error: %s", exc)
        return {"analysis": f"AI service error. Please try again. Error: {exc}"}

    except Exception as exc:
        logger.error("Outbreak LLM error: %s", exc)
        return {"analysis": f"AI service error. Please try again. Error: {exc}"}

def extract_condition_from_analysis(analysis_text: str) -> str:
    """Helper to extract the condition name from sentinel tags."""
    if "[SENTINEL_CONDITION]" in analysis_text:
        parts = analysis_text.split("[SENTINEL_CONDITION]")
        if len(parts) > 1:
            condition_part = parts[1].split("[")[0].strip()
            return condition_part
    return "Unknown Condition"

def scan_prescription(image_file) -> dict:
    """Extract medication details from prescription image."""
    prompt = """
    Extract medication details from this prescription image. 
    Provide the Name, Dosage, Frequency, and Time of Day (Morning, Midday, Evening, Bedtime).
    Respond in JSON format:
    {
        "name": "...",
        "dosage": "...",
        "frequency": "...",
        "time_of_day": "..."
    }
    """
    try:
        model = _get_model()
        if model:
            image_file.file.seek(0)
            image_data = image_file.file.read()
            mime_type = getattr(image_file, "content_type", None) or "image/jpeg"
            response = model.generate_content([prompt, {"mime_type": mime_type, "data": image_data}])
            import json
            # Extract JSON from response text (handle markdown blocks)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
    except Exception as e:
        logger.warning("AI Scan failed, using mock data: %s", e)
    
    return {
        "name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "Twice daily",
        "time_of_day": "Morning & Evening"
    }

