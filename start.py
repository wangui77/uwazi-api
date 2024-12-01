import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from config.config import Config
from config.database.seed import seed
from middlewares import middlewares
from routes.auth import register_auth_routes
from routes.health import register_general_routes
from services.db_service import db


class App:
    def __init__(self):
        load_dotenv()

        # Initialize the Flask app
        self.app = Flask(__name__)

        # Configure the app with settings from config/config.py
        self.app.config.from_object(Config)

        # Setup API security
        CORS(self.app)

        # Setup database tables, database connection uri and seeds
        self.app.config["SQLALCHEMY_DATABASE_URI"] = Config.get_db_uri()

        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            seed()

        # Register routes
        register_general_routes(self.app)
        register_auth_routes(self.app)

        # Register middlewares
        middlewares(self.app)

    def get(self):
        environment = os.getenv("FLASK_ENV", "production")
        flask_port = int(os.getenv("FLASK_PORT", 8080))
        debug_mode = environment == "development"

        return self.app, debug_mode, flask_port


app, debug_mode, flask_port = App().get()

app.run(host="0.0.0.0", port=flask_port, debug=debug_mode)
