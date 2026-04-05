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

try:
    response = supabase.table("medical_forms").select("*").limit(5).execute()
    print(f"Medical Forms entries: {len(response.data)}")
    for row in response.data:
        print(f"Email: {row.get('email') or row.get('user_email')}")
except Exception as e:
    print(f"Error: {e}")
