import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(url, key)

TEST_EMAIL = "fabricants9747@gmail.com" # Existing in medical_forms

print(f"--- Attempting to verify uniqueness for {TEST_EMAIL} ---")

try:
    # 1. Fetch current steps
    res_init = supabase.table("user_vitals").select("*").eq("user_email", TEST_EMAIL).execute()
    init_steps = res_init.data[0]["steps"] if res_init.data else 0
    print(f"Initial steps: {init_steps}")
    
    # 2. Upsert with new steps
    new_steps = init_steps + 100
    data = {
        "user_email": TEST_EMAIL,
        "steps": new_steps,
        "heart_rate": 70,
        "sleep_hours": 8.0,
        "calories": 2000,
        "source": "system_test_upsert"
    }
    
    print(f"Upserting {new_steps} steps...")
    res_upsert = supabase.table("user_vitals").upsert(data, on_conflict="user_email").execute()
    
    # 3. Verify
    res_final = supabase.table("user_vitals").select("*").eq("user_email", TEST_EMAIL).execute()
    final_steps = res_final.data[0]["steps"]
    count = len(res_final.data)
    
    print(f"Final steps: {final_steps}")
    print(f"Records found for {TEST_EMAIL}: {count}")
    
    if count == 1 and final_steps == new_steps:
        print("✅ SUCCESS: Upsert working correctly on existing email.")
    else:
        print("❌ FAILURE: Upsert logic not working as expected.")

except Exception as e:
    print(f"❌ ERROR: {e}")
