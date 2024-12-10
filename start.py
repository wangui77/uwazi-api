import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config.config import Config
from config.database.seed import seed
from middlewares import middlewares
from routes import register_routes
from services.db_service import db


class App:
    def __init__(self):
        load_dotenv()

        # Initialize the Flask app
        self.app = Flask(__name__)

        # Configure the app with settings from config/config.py
        self.app.config.from_object(Config)

        # Setup API security
    
        CORS(self.app, resources={r"/api/*": {"origins": ["http://localhost:4200", "  https://a758-41-90-101-26.ngrok-free.app "]}})


        # Setup JWT management
        self.app.config["JWT_SECRET_KEY"] = os.getenv(
            "SECRET_KEY", "9VV69kGgnBQkt23Rn8Gx2oweiutxFo4prbVY-EbSt8Q="
        )
        self.app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
        self.app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

        # Initialize JWTManager with the Flask app
        jwt = JWTManager(self.app)

        # Setup database tables, database connection uri and seeds
        self.app.config["SQLALCHEMY_DATABASE_URI"] = Config.get_db_uri()

        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            seed()

        # Register routes
        register_routes(self.app)

        # Register middlewares
        middlewares(self.app)

    def get(self):
        environment = os.getenv("FLASK_ENV", "production")
        flask_port = int(os.getenv("FLASK_PORT", 8080)) #use render's port env variable
        debug_mode = environment == "development"

        return self.app, debug_mode, flask_port


app, debug_mode, flask_port = App().get()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=flask_port, debug=debug_mode)
