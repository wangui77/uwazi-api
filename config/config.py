import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    # Disable modification tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    DB_HOST = os.getenv("POSTGRES_HOST", "database")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "uwazi_db")
    DB_USER = os.getenv("POSTGRES_USER", "uwazi_user")
    DB_PASSWORD = os.getenv(
        "POSTGRES_PASSWORD", "uwazi_password"
    )

    @staticmethod
    def get_db_uri():
        # Build the database URI manually using environment variables
        default_uri = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
        # Use DATABASE_URL if set, otherwise fallback to the manually built URI
        return os.getenv("DATABASE_URL", default_uri)