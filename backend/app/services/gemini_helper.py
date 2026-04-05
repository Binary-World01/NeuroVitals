"""
Groq AI Helper — Handles LLM calls for risk prediction.
Migrated from neurofit_risk_engine14/gemini_helper.py
Function name kept as call_gemini for backward compatibility.
"""
import os
import json
import re
import requests
from app.config import settings

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT = 120

# Groq token limit — keep prompt under this many characters (approx 4 chars per token)
MAX_PROMPT_CHARS = 20000


def trim_prompt(prompt: str) -> str:
    """
    If the prompt is too large for Groq, trim the historical_trends section
    which is the biggest part but least important for the prediction.
    """
    if len(prompt) <= MAX_PROMPT_CHARS:
        return prompt

    try:
        user_data_marker = "User Data:"
        marker_pos = prompt.find(user_data_marker)
        if marker_pos == -1:
            return prompt[:MAX_PROMPT_CHARS]

        system_part = prompt[:marker_pos + len(user_data_marker)]
        user_data_str = prompt[marker_pos + len(user_data_marker):].strip()

        user_data = json.loads(user_data_str)

        # Trim historical_trends — keep only last 7 daily logs instead of 30
        if "historical_trends" in user_data:
            ht = user_data["historical_trends"]
            if "daily_logs" in ht and len(ht["daily_logs"]) > 7:
                ht["daily_logs"] = ht["daily_logs"][:7]
            ht.pop("recent_predictions", None)
            user_data["historical_trends"] = ht

        # Trim medical_records — keep only last 5
        if "medical_records" in user_data and len(user_data["medical_records"]) > 5:
            user_data["medical_records"] = user_data["medical_records"][:5]

        trimmed_prompt = system_part + "\n" + json.dumps(user_data, indent=2)

        if len(trimmed_prompt) > MAX_PROMPT_CHARS:
            if "historical_trends" in user_data:
                user_data.pop("historical_trends", None)
            trimmed_prompt = system_part + "\n" + json.dumps(user_data, indent=2)

        if len(trimmed_prompt) > MAX_PROMPT_CHARS:
            trimmed_prompt = trimmed_prompt[:MAX_PROMPT_CHARS]

        print(f"[INFO] Prompt trimmed from {len(prompt)} to {len(trimmed_prompt)} chars")
        return trimmed_prompt

    except Exception as e:
        print(f"[WARN] Could not trim prompt intelligently: {e}. Hard truncating.")
        return prompt[:MAX_PROMPT_CHARS]


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'(\{.*\})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = text

    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    return json.loads(json_str)


def call_gemini(prompt: str) -> dict:
    """
    Call Groq API with the given prompt and return parsed JSON result.
    Function name kept as call_gemini for backward compatibility.
    """
    if not GROQ_API_KEY:
        return _error_response("GROQ_API_KEY not configured. Set it in .env")

    prompt = trim_prompt(prompt)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.0,
        "max_tokens": 8192,
        "stream": False
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        if not response.ok:
            print(f"[DEBUG] Status Code : {response.status_code}")
            print(f"[DEBUG] Error Body  : {response.text}")
            response.raise_for_status()

        data = response.json()
        raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not raw_text:
            return _error_response("Groq returned an empty response.")

        try:
            return extract_json(raw_text)
        except json.JSONDecodeError as e:
            return _error_response(
                f"JSON parsing error: {e}. Raw response: {raw_text[:300]}..."
            )

    except requests.exceptions.RequestException as e:
        return _error_response(f"Groq API request failed: {e}")
    except Exception as e:
        return _error_response(f"Unexpected error: {e}")


def _error_response(message: str) -> dict:
    """Return a structured error response matching the expected schema."""
    return {
        "risk_percentages": {},
        "risk_level": "Error",
        "key_reasons": [message],
        "trend_prediction": {},
        "recommendations": [
            "Check your Groq API key and internet connection, then try again."
        ],
    }
