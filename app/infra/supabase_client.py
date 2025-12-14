from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required. Please set them in a .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

FOCUSNFE_BASE_URL = os.getenv("FOCUSNFE_BASE_URL")
FOCUSNFE_TOKEN = os.getenv("FOCUSNFE_TOKEN")

if not FOCUSNFE_BASE_URL or not FOCUSNFE_TOKEN:
    raise RuntimeError("FOCUSNFE_BASE_URL and FOCUSNFE_TOKEN must be set in environment variables.")
