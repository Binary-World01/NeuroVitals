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

# Check user_vitals rows
try:
    response = supabase.table("user_vitals").select("*").execute()
    print(f"Total rows in user_vitals: {len(response.data)}")
    for row in response.data:
        print(f"Email: {row['user_email']}, Steps: {row['steps']}, ID: {row['id']}")
except Exception as e:
    print(f"Error: {e}")
