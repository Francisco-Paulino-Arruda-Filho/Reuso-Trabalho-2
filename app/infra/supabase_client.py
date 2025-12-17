from supabase import ClientOptions, create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required. Please set them in a .env file.")

options = ClientOptions(
    function_client_timeout=30.0,
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
