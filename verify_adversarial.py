import requests
import json

def test_adversarial_debate():
    url = "http://localhost:8000/api/adversarial/debate"
    payload = {
        "patient_id": "test_user@example.com",
        "age": 45,
        "gender": "Male",
        "symptoms": "Severe headache, sudden confusion, and right-sided weakness",
        "medical_history": ["Hypertension"],
        "current_medications": ["Lisinopril"]
    }
    
    print(f"Testing {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success! Debate result received.")
            print(f"Prosecutor Diagnosis: {result['prosecutor']['diagnosis']}")
            print(f"Defense Diagnosis: {result['defense']['alternative_diagnosis']}")
            print(f"Verdict: {result['verdict']['final_diagnosis']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_adversarial_debate()
