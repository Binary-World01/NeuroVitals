import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("Testing sign up with metadata...")
try:
    # Use a fresh unique email
    email = "test_meta_user_99@example.com"
    response = supabase.auth.sign_up({
        "email": email, 
        "password": "password123",
        "options": { "data": { "full_name": "Test User" } }
    })
    print("Sign up response:", response)
except Exception as e:
    print(f"Sign up error: {e}")
