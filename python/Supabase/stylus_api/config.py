# backend/stylus_api/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    WEATHER = os.getenv("WEATHER")
    GEM = os.getenv("GEMINI_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
    HUGGING_FACE = os.getenv("HUGGING_FACE")
