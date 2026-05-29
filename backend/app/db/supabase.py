# supabase.py
# Creates one Supabase client that entire app shares
# Imported by other service files

from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

# Single client instance
client = create_client(SUPABASE_URL, SUPABASE_KEY)