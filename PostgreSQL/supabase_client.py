from supabase import create_client, Client

# Your Supabase credentials
url: str = "https://cejlsybbdezcdmrgiqxv.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNlamxzeWJiZGV6Y2RtcmdpcXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3Mjc2MDIsImV4cCI6MjA2OTMwMzYwMn0.OyYVvM0zM7q8rTKklYGYKVfv7cm8R4twODVy_zxOwcU"

# Create the Supabase client
supabase: Client = create_client(url, key)

# Test the connection
try:
    # Example: fetch data from a table
    response = supabase.table('esp32_boards').select("*").execute()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")

