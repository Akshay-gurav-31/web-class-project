import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'swapnilgurav8957',  # Change this to your MySQL root password
    'database': 'music_academy_db'
}

def create_database_and_table():
    # First, connect without specifying a database to create the database
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS music_academy_db")
            print("Database 'music_academy_db' created or already exists.")
            
            # Close the connection and reconnect to the specific database
            cursor.close()
            connection.close()
            
            # Now connect to the specific database
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            
            # Create students table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                current_course VARCHAR(100) DEFAULT 'Guitar Course',
                joining_date DATE,
                certificate_generated BOOLEAN DEFAULT FALSE,
                certificate_file LONGBLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_query)
            print("Table 'students' created or already exists.")
            
            # Close connections
            cursor.close()
            connection.close()
            print("Database setup completed successfully!")
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        
if __name__ == "__main__":
    create_database_and_table()

# This file is no longer needed as we're using Supabase instead of MySQL
# Supabase handles database creation and schema management through its dashboard
# You can delete this file or keep it for reference
print("This setup script is no longer needed as we're using Supabase instead of MySQL.")
print("Please ensure your Supabase project has a 'students' table with the following schema:")
print("""
Table: students
- id (int, primary key, auto-increment)
- name (varchar)
- email (varchar, unique)
- password (varchar)
- current_course (varchar)
- joining_date (date)
- certificate_generated (boolean)
- certificate_file (bytea or longblob)
- enrolled_courses (json)
- created_at (timestamp)
""")
