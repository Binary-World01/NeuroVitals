import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
supabase = create_client(url, key)

try:
    print("Attempting to sign in...")
    # we just provide dummy credentials because even if it fails with 'Invalid login credentials',
    # it shouldn't fail with 'Database error querying schema' unless the schema is broken.
    response = supabase.auth.sign_in_with_password({"email": "test@example.com", "password": "password123"})
    print(response)
except Exception as e:
    print(f"Auth Error: {e}")
