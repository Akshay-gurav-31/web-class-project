from supabase import create_client, Client
import json

# Supabase Config
SUPABASE_URL = "https://siolenykcgnnthwjongt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpb2xlbnlrY2dubnRod2pvbmd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3NDYyNzEsImV4cCI6MjA3ODMyMjI3MX0.DES4jyP4UDwTzqGnns_kouhhKdmFk87a-CVHhHsNQFI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_students_table():
    print("Creating students table in Supabase...")
    print("Note: In Supabase, tables are created through the dashboard or SQL editor.")
    print("Please run the following SQL in your Supabase SQL editor:")
    print("""
-- Create the students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    current_course VARCHAR(100),
    joining_date DATE,
    enrolled_courses JSONB,
    certificate_generated BOOLEAN DEFAULT FALSE,
    certificate_file BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
""")
    
    # Test connection
    try:
        # Insert a test record to verify the connection
        test_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "hashed_password_example",
            "current_course": "Guitar Course",
            "joining_date": "2023-01-01",
            "enrolled_courses": json.dumps([]),
            "certificate_generated": False
        }
        
        # Check if test user already exists
        response = supabase.table("students").select("*").eq("email", "test@example.com").execute()
        if not response.data:
            # Insert test record
            response = supabase.table("students").insert(test_data).execute()
            print("Test record inserted successfully!")
            
            # Clean up test record
            supabase.table("students").delete().eq("email", "test@example.com").execute()
            print("Test record cleaned up.")
        else:
            print("Connection successful! Table already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure your Supabase credentials are correct and the table exists.")

if __name__ == "__main__":
    create_students_table()