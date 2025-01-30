import os

from dotenv import load_dotenv

load_dotenv()


class Config:

    # Disable modification tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    DB_HOST = os.getenv("POSTGRES_HOST", "dpg-cu3sifpu0jms73dopl50-a")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "uwazidb_4amx")
    DB_USER = os.getenv("POSTGRES_USER", "uwazidb_4amx_user")
    DB_PASSWORD = os.getenv(
        "POSTGRES_PASSWORD", "44dJk79gN61pm3hkf1oVwmnVcTnZx3Mu"
    )

    @staticmethod
    def get_db_uri():
        default_uri = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
        return os.getenv("DATABASE_URL", default_uri)
