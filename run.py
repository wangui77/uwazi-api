import os

from dotenv import load_dotenv

from app import create_app

# Load environment variables from the .env file
load_dotenv()

# Determine the Flask environment
env = os.getenv("FLASK_ENV", "production")

DEBUG_MODE = env == "development"
FLASK_PORT = os.getenv("PORT", 8080)

# Create the Flask app
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=DEBUG_MODE)
