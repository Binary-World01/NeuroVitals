import os
import requests
import json
from dotenv import load_dotenv

# Load .env from the parent directory
load_dotenv("c:/Users/Parth/OneDrive/Desktop/PuneHack - Copy (2)vitals/neuro-vitals/.env")

token = os.getenv("GITHUB_TOKEN")
url = os.getenv("GITHUB_API_URL", "https://models.inference.ai.azure.com")

print(f"Token present: {bool(token)}")
print(f"URL: {url}")

models_to_try = [
    "google/gemini-1.5-flash",
    "gemini-1.5-flash",
    "Gemini-1.5-Flash",
    "gpt-4o-mini",
    "gpt-4o"
]

for model in models_to_try:
    print(f"\nTesting model: {model}")
    try:
        resp = requests.post(
            f"{url}/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Hello, are you working?"}],
                "temperature": 0.2,
                "max_tokens": 100
            },
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        if resp.ok:
            print("Success!")
            # print(resp.json()["choices"][0]["message"]["content"])
            break
        else:
            print(f"Error Body: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")
