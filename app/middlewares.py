from functools import wraps

from flask import jsonify, request

from app.services.jwt_service import jwt_service


def authentication_middleware(app):
    """
    Middleware to enforce authentication globally except for specific routes.
    """
    @app.before_request
    def before_request():
        # Skip middleware for specific public routes
        public_endpoints = ["auth.login", "auth.register", "health"]
        if request.endpoint in public_endpoints:
            return

        # Get the JWT from the Authorization header or cookie
        token = None
        if "Authorization" in request.headers and request.headers["Authorization"].startswith("Bearer "):
            token = request.headers["Authorization"].split(" ")[1]
        elif "access_token" in request.cookies:
            token = request.cookies.get("access_token")

        # Validate the token
        if not token:
            return jsonify({"error": "Unauthorized", "message": "Missing token"}), 401

        is_valid, error_message = jwt_service.is_token_valid(token, "access")
        if not is_valid:
            return jsonify({"error": "Unauthorized", "message": error_message}), 401
