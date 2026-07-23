from supabase import create_client, Client
from config import settings

# Create one Supabase client for the whole app so routes reuse the same config.
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)