from supabase import create_client, Client
from config.config import Settings

settings = Settings()

def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
