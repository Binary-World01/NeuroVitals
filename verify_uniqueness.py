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

# Try to add a unique constraint if it doesn't exist
# We can't do this directly easily via supabase-py without RPC or Raw SQL
# But we can check if it works.

TEST_EMAIL = "system_test_unique@example.com"

print(f"--- Attempting to verify uniqueness for {TEST_EMAIL} ---")

data1 = {
    "user_email": TEST_EMAIL,
    "steps": 100,
    "heart_rate": 60,
    "sleep_hours": 8.0,
    "calories": 2000,
    "source": "system_test"
}

try:
    # 1. Insert first
    print("Inserting first record...")
    res1 = supabase.table("user_vitals").upsert(data1, on_conflict="user_email").execute()
    print(f"Insert 1: {res1.data}")
    
    # 2. Update with same email
    data2 = data1.copy()
    data2["steps"] = 500
    print("Inserting second record with same email (upsert)...")
    res2 = supabase.table("user_vitals").upsert(data2, on_conflict="user_email").execute()
    print(f"Insert 2: {res2.data}")
    
    # 3. Check count
    res_check = supabase.table("user_vitals").select("*").eq("user_email", TEST_EMAIL).execute()
    print(f"Records found for {TEST_EMAIL}: {len(res_check.data)}")
    
    if len(res_check.data) == 1 and res_check.data[0]["steps"] == 500:
        print("✅ SUCCESS: Uniqueness and Upsert working correctly.")
    else:
        print("❌ FAILURE: Redundant records or update failed.")

except Exception as e:
    print(f"❌ ERROR: {e}")
finally:
    # Clean up
    supabase.table("user_vitals").delete().eq("user_email", TEST_EMAIL).execute()
