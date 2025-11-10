# Music Classes Application

This is a Flask-based web application for managing music classes. It supports multiple instruments (guitar, electric guitar, piano, ukulele) with dedicated dashboards and syllabus pages.

## Features
- User enrollment and authentication (login/signup)
- Course management and content delivery
- Certificate generation (using PDF and QR code)
- Admin panel for management

## Migration from MySQL to Supabase

This application has been migrated from MySQL to Supabase for database management. The following changes were made:

1. Removed MySQL dependencies and configuration
2. Added Supabase client library
3. Updated all database operations to use Supabase REST API
4. Modified data models to match Supabase requirements

## Setup Instructions

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create the required table in Supabase:
   - Go to your Supabase dashboard
   - Navigate to the SQL editor
   - Run the following SQL query:
   
   ```sql
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
   
   CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
   ```

3. Run the application:
   ```
   python app.py
   ```

## Environment Variables

The application uses the following Supabase configuration:
- SUPABASE_URL: https://siolenykcgnnthwjongt.supabase.co
- SUPABASE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpb2xlbnlrY2dubnRod2pvbmd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3NDYyNzEsImV4cCI6MjA3ODMyMjI3MX0.DES4jyP4UDwTzqGnns_kouhhKdmFk87a-CVHhHsNQFI

## Directory Structure
- `app.py`: Main application entry point
- `templates/`: HTML templates including:
  - `/dashboard`: Instrument-specific dashboards
  - `/syllabus`: Syllabus pages per instrument
  - Other pages: login, signup, course, certificate, etc.
- `static/style.css`: Stylesheet for frontend
- `init_supabase.py`: Supabase initialization script (for reference)

## Dependencies
- Flask
- PyPDF2
- reportlab
- qrcode
- Werkzeug
- Pillow
- gunicorn
- supabase