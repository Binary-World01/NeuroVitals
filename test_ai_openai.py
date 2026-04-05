from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = os.getenv("GITHUB_API_URL", "https://models.inference.ai.azure.com")

def test_model(model_name):
    print(f"Testing model: {model_name} at {BASE_URL}")
    try:
        client = OpenAI(base_url=BASE_URL, api_key=TOKEN)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "How are you? Fix your answer to 2 words."}],
            max_tokens=10
        )
        print(f"Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Failed: {e}")

test_model("gpt-4o-mini")
test_model("gpt-4o")
test_model("google/gemini-1.5-flash")
