import os
from supabase import create_client
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(url, key)

try:
    response = supabase.table("user_vitals").select("*").execute()
    data = response.data
    print(f"Total rows in user_vitals: {len(data)}")
    
    emails = [row['user_email'] for row in data]
    counts = Counter(emails)
    
    redundant = {email: count for email, count in counts.items() if count > 1}
    
    if redundant:
        print("🚩 REDUNDANT RECORDS FOUND:")
        for email, count in redundant.items():
            print(f"  - {email}: {count} records")
            # Show the records
            records = [r for r in data if r['user_email'] == email]
            for r in records:
                print(f"    - ID: {r['id']}, Steps: {r['steps']}, Updated At: {r['updated_at']}")
    else:
        print("✅ No redundant records found (single row per email confirmed).")

except Exception as e:
    print(f"Error: {e}")
