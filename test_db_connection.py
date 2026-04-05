import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key Present: {bool(key)}")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    supabase = create_client(url, key)
    # Try to list tables or do a simple query
    response = supabase.table("user_vitals").select("*").limit(1).execute()
    print("Connection Successful!")
    print(f"Data: {response.data}")
except Exception as e:
    print(f"Connection Failed: {e}")
