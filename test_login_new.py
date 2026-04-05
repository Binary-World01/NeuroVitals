import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("Testing sign in for new user...")
try:
    response = supabase.auth.sign_in_with_password({"email": "test_new_user_12345@example.com", "password": "password123"})
    print("Sign in response:", response)
except Exception as e:
    print(f"Sign in error: {e}")
