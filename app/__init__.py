from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from app.config import Config
from app.middlewares import authentication_middleware
from app.routes import register_blueprints
from app.services.db_service import db


def create_app():
    """
    Factory method to create the Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)  # Load configuration from Config class

    # Dynamically set the SQLAlchemy URI
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.get_db_uri()

    # Initialize CORS
    CORS(app)

    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    register_blueprints(app)

    # Apply the authentication middleware globally
    authentication_middleware(app)

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "healthy"}, 200

    return app
