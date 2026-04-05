import requests
import json
import time

BASE_URL = "http://localhost:8000/api/vitals"
TEST_EMAIL = "fabricants974@gmail.com"

def test_vitals_sync():
    print(f"--- Testing Vitals Sync for {TEST_EMAIL} ---")
    
    # 1. Clean up if exists
    print("Cleaning up old test data...")
    requests.delete(f"{BASE_URL}/delete-vitals/{TEST_EMAIL}")
    
    # 2. Initial Save
    payload1 = {
        "user_email": TEST_EMAIL,
        "steps": 1000,
        "heart_rate": 70,
        "sleep_hours": 7.5,
        "calories": 2000,
        "source": "manual_test"
    }
    print(f"Sending initial vitals: {payload1}")
    res1 = requests.post(f"{BASE_URL}/save-vitals", json=payload1)
    print(f"Response: {res1.status_code} - {res1.text}")
    assert res1.status_code == 200
    
    # 3. Verify record count (should be 1)
    res_get = requests.get(f"{BASE_URL}/get-vitals/{TEST_EMAIL}")
    data_get = res_get.json()["data"]
    print(f"Records found: {len(data_get)}")
    assert len(data_get) == 1
    assert data_get[0]["steps"] == 1000
    
    # 4. Update Save (Redundant record check)
    payload2 = {
        "user_email": TEST_EMAIL,
        "steps": 5000,
        "heart_rate": 75,
        "sleep_hours": 8.0,
        "calories": 2500,
        "source": "manual_test_update"
    }
    print(f"Sending updated vitals: {payload2}")
    res2 = requests.post(f"{BASE_URL}/save-vitals", json=payload2)
    print(f"Response: {res2.status_code} - {res2.text}")
    assert res2.status_code == 200
    
    # 5. Verify record count still 1 and values updated
    res_get2 = requests.get(f"{BASE_URL}/get-vitals/{TEST_EMAIL}")
    data_get2 = res_get2.json()["data"]
    print(f"Records found after update: {len(data_get2)}")
    assert len(data_get2) == 1
    assert data_get2[0]["steps"] == 5000
    assert data_get2[0]["source"] == "manual_test_update"
    
    print("\n✅ SUCCESS: Single row per email maintained and values updated correctly.")

if __name__ == "__main__":
    try:
        test_vitals_sync()
    except Exception as e:
        print(f"\nFAILURE: {e}")
