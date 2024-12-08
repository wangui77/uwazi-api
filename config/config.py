import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Config:
    # Disable modification tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")  # Get DATABASE_URL from .env

    @staticmethod
    def get_db_uri():
        # Return DATABASE_URL directly
        return Config.DATABASE_URL
