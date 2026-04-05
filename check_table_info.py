import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

# Note: Supabase REST API doesn't easily expose information_schema.
# But we can try to get hints by looking at the data.

supabase = create_client(url, key)

try:
    response = supabase.table("user_vitals").select("*").limit(5).execute()
    if response.data:
        print("Columns found in user_vitals:")
        for key in response.data[0].keys():
            print(f"- {key}: {type(response.data[0][key])}")
    else:
        print("No data in user_vitals to infer columns.")
except Exception as e:
    print(f"Error: {e}")
