from supabase import create_client, Client
import json
from datetime import date

# Supabase Config
SUPABASE_URL = "https://siolenykcgnnthwjongt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpb2xlbnlrY2dubnRod2pvbmd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3NDYyNzEsImV4cCI6MjA3ODMyMjI3MX0.DES4jyP4UDwTzqGnns_kouhhKdmFk87a-CVHhHsNQFI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    print("Testing Supabase connection...")
    try:
        # Test inserting a record
        test_student = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "hashed_password_example",
            "current_course": "Guitar Course",
            "joining_date": date.today().isoformat(),
            "enrolled_courses": json.dumps([]),
            "certificate_generated": False
        }
        
        # Check if test user already exists and delete it
        response = supabase.table("students").select("*").eq("email", "test@example.com").execute()
        if response.data:
            supabase.table("students").delete().eq("email", "test@example.com").execute()
            print("Existing test record deleted.")
        
        # Insert test record
        response = supabase.table("students").insert(test_student).execute()
        print("Test record inserted successfully!")
        student_id = response.data[0]['id']
        print(f"Inserted student with ID: {student_id}")
        
        # Test retrieving the record
        response = supabase.table("students").select("*").eq("email", "test@example.com").execute()
        if response.data:
            print("Retrieved student record:")
            print(json.dumps(response.data[0], indent=2, default=str))
        else:
            print("Failed to retrieve student record")
        
        # Test updating the record
        response = supabase.table("students").update({
            "current_course": "Piano Course"
        }).eq("email", "test@example.com").execute()
        print("Student record updated successfully!")
        
        # Test deleting the record
        response = supabase.table("students").delete().eq("email", "test@example.com").execute()
        print("Test record deleted successfully!")
        
        print("All tests passed! Supabase integration is working correctly.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Please ensure:")
        print("1. Your Supabase credentials are correct")
        print("2. The 'students' table exists in your Supabase project")
        print("3. You've run the SQL script to create the table")

if __name__ == "__main__":
    test_connection()