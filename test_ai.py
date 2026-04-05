import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = os.getenv("GITHUB_API_URL", "https://models.inference.ai.azure.com")

def test_endpoint(url, model):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [{"role": "user", "content": "Say hi"}],
        "model": model,
        "temperature": 1,
        "max_tokens": 10
    }
    print(f"Testing URL: {url} with model: {model}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

# Try the GitHub Models endpoint WITHOUT /v1
test_endpoint(f"{BASE_URL}/chat/completions", "gpt-4o-mini")
test_endpoint(f"{BASE_URL}/chat/completions", "gpt-4o")
test_endpoint(f"{BASE_URL}/chat/completions", "google/gemini-1.5-flash")
