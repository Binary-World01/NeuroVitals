import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("1. Testing sign_in...")
try:
    response = supabase.auth.sign_in_with_password({"email": "fabricants974@gmail.com", "password": "password123"})
    print("Sign in response:", response)
except Exception as e:
    print(f"Sign in error: {e}")

print("2. Testing users table select...")
try:
    response = supabase.table('users').select('*').limit(1).execute()
    print("Users table response:", response)
except Exception as e:
    print(f"Users table error: {e}")

print("3. Testing arbitrary table select...")
try:
    response = supabase.table('profiles').select('*').limit(1).execute()
    print("Profiles table response:", response)
except Exception as e:
    print(f"Profiles table error: {e}")
