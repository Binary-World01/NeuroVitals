import sys
import os

# Add backend and root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.adversarial_engine import adversarial_engine

def test_engine_schema():
    print("Testing Adversarial Engine Schema...")
    
    # Mock data
    patient_data = {
        "age": 30,
        "gender": "Male",
        "symptoms": "High fever, persistent cough, fatigue",
        "medical_history": ["None"]
    }
    
    # Force mock mode for testing if keys are missing, 
    # but the current engine already handles that in __init__
    
    print("\nRunning Debate Simulation...")
    result = adversarial_engine.run_debate(patient_data)
    
    print("\n[VERDICT SCHEMA CHECK]")
    verdict = result.get("verdict", {})
    required_keys = ["verdict", "confidence", "synthesis", "next_step", "highlights"]
    
    success = True
    for key in required_keys:
        if key in verdict:
            print(f"  [PASS] Found key: {key}")
        else:
            print(f"  [FAIL] Missing key: {key}")
            success = False
            
    print("\n[RESULT DATA]")
    print(f"  Prosecutor Diagnosis: {result['prosecutor']['diagnosis']}")
    print(f"  Defense Diagnosis: {result['defense'].get('diagnosis', 'N/A')}")
    print(f"  Judge Verdict: {verdict.get('verdict')}")
    
    if success:
        print("\nSUCCESS: All required schema keys are present!")
    else:
        print("\nFAILURE: Some schema keys are missing.")
        sys.exit(1)

if __name__ == "__main__":
    test_engine_schema()
