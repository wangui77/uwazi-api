import os

from dotenv import load_dotenv

# Load environment variables from the appropriate .env file
environment = os.getenv("FLASK_ENV", "development")
dotenv_file = ".env.ci" if environment == "testing" else ".env"
load_dotenv(dotenv_file)


class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "9VV69kGgnBQkt23Rn8Gx2oweiutxFo4prbVY-EbSt8Q="
    )
    # Disable modification tracking overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    # Database type: postgres or sqlserver
    DB_TYPE = os.getenv("DB_TYPE", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "uwazi_db")
    DB_USER = os.getenv("DB_USER", "uwazi_user")
    DB_PASSWORD = os.getenv(
        "DB_PASSWORD", "uwazi_password"
    )

    @staticmethod
    def get_db_uri():
        """
        Dynamically construct the SQLAlchemy database URI based on DB_TYPE.
        """
        if Config.DB_TYPE == "postgres":
            return (
                f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
                f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
            )
        elif Config.DB_TYPE == "sqlserver":
            return (
                f"mssql+pyodbc://{Config.DB_USER}:{Config.DB_PASSWORD}@"
                f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
            )
        else:
            raise ValueError(f"Unsupported database type: {Config.DB_TYPE}")
