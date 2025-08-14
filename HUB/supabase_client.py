from supabase import create_client, Client
from database_supabase import Database

# Your Supabase credentials
url: str = "https://.supabase.co"
key: str = ""

# Create the Supabase client
supabase: Client = create_client(url, key)

# Test the connection
try:
    # Example: fetch data from a table
    response = supabase.table('esp32_boards').select("*").execute()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")

