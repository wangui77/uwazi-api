# Blue print initialization
from app.routes.auth import auth_bp
from app.routes.hospital import hospital_bp
from app.routes.insurance import insurance_bp
from flask import Flask


def register_blueprints(app: Flask):
    """
    Register all blueprints with the Flask application.
    """
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(hospital_bp, url_prefix="/hospital")
    app.register_blueprint(insurance_bp, url_prefix="/insurance")
