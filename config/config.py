import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    # Disable modification tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    DB_HOST = os.getenv("POSTGRES_HOST", "dpg-cudn4naj1k6c73cqgn80-a")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "uwazidb_gxk6")
    DB_USER = os.getenv("POSTGRES_USER", "uwazidb_gxk6_user")
    DB_PASSWORD = os.getenv(
        "POSTGRES_PASSWORD", "mKjdbE9lTrlV42bBb5pEtB6DEp4nGsCO"
    )

    @staticmethod
    def get_db_uri():
        default_uri = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
        return os.getenv("DATABASE_URL", default_uri)
