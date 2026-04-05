import requests
import json

def test_adversarial_debate():
    url = "http://localhost:8000/api/adversarial/debate"
    payload = {
        "patient_id": "test_user@example.com",
        "age": 30,
        "gender": "Male",
        "symptoms": "Severe headache, sensitivity to light, nausea",
        "medical_history": ["Migraines in childhood"]
    }
    
    print(f"Testing Adversarial Debate at {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success! Result Summary:")
            print(f"Prosecutor Diagnosis: {result['prosecutor']['diagnosis']}")
            print(f"Prosecutor Confidence: {result['prosecutor']['confidence']}%")
            print(f"Prosecutor Points: {len(result['prosecutor'].get('points', []))}")
            
            print(f"Defense Diagnosis: {result['defense'].get('alternative_diagnosis') or result['defense'].get('diagnosis')}")
            print(f"Defense Confidence: {result['defense']['confidence']}%")
            print(f"Defense Points: {len(result['defense'].get('points', []))}")
            
            print(f"Judge Verdict: {result['verdict']['verdict']}")
            print(f"Judge Confidence: {result['verdict']['confidence']}%")
            print(f"Next Step: {result['verdict']['next_step']}")
            return True
        else:
            print(f"Failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        print("Note: Ensure the backend is running on http://localhost:8000")
        return False

if __name__ == "__main__":
    test_adversarial_debate()
