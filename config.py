import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Validate the environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Missing required environment variables. Please make sure SUPABASE_URL and SUPABASE_KEY are set in your .env file."
    )