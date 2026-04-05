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

TEST_EMAIL = "test_constraint@example.com"

try:
    # 1. Insert first
    print(f"Inserting first record for {TEST_EMAIL}...")
    supabase.table("user_vitals").insert({"user_email": TEST_EMAIL, "steps": 100}).execute()
    
    # 2. Try to insert second (SHOULD FAIL if constraint exists)
    print("Attempting to insert second record for SAME email (should fail if UNIQUE constraint exists)...")
    supabase.table("user_vitals").insert({"user_email": TEST_EMAIL, "steps": 200}).execute()
    print("🚩 FAILURE: Inserted duplicate record! No UNIQUE constraint found on user_email.")

except Exception as e:
    if "23505" in str(e) or "duplicate key" in str(e).lower():
        print("✅ SUCCESS: UNIQUE constraint is active on user_email.")
    else:
        print(f"❓ ERROR: {e}")
finally:
    # Clean up
    supabase.table("user_vitals").delete().eq("user_email", TEST_EMAIL).execute()
