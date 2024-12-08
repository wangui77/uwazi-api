import psycopg2
from config import Config  # Assuming you have your Config class in config.py

def test_db_connection():
    try:
        # Establish the connection to the database
        conn = psycopg2.connect(
            host=Config.DB_HOST,         # Your database host (e.g., "localhost" or "database" in Docker)
            port=Config.DB_PORT,         # Your PostgreSQL port (default is 5432)
            dbname=Config.DB_NAME,       # Your database name
            user=Config.DB_USER,         # Your PostgreSQL username
            password=Config.DB_PASSWORD  # Your PostgreSQL password
        )

        # If the connection is successful, print success message
        print("Connection successful!")

        # Close the connection
        conn.close()

    except Exception as e:
        # If an error occurs, print the error message
        print(f"Error: {e}")

# Run the test
test_db_connection()
