from flask import jsonify, request
from flask_jwt_extended import (jwt_required, set_access_cookies,
                                set_refresh_cookies)

from services.jwt_service import jwt_service


def register_general_routes(app):
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "healthy"}, 200
