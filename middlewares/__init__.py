import json
from functools import wraps

from flask import jsonify, request
from services.jwt_service import jwt_service


def middlewares(app):
    @app.before_request
    def logging_middleware():
        try:
            # Make a copy of `request.__dict__` to avoid runtime modification issues
            request_dict = {key: str(value)
                            for key, value in dict(request.__dict__).items()}

            # Pretty-print the serialized dictionary
            # print(json.dumps(request_dict, indent=4), flush=True)
        except Exception as e:
            print(f"Error while serializing request.__dict__: {e}", flush=True)

    @app.before_request
    def auth_check_middleware():
        # Skip middleware for specific public routes
        public_endpoints = [
            "/auth/login",
            "/health"
        ]
        if request.path in public_endpoints:
            return

        # Validate token
        token = jwt_service.get_token_from_request(request)
        if not token:
            return jsonify({"error": "Unauthorized", "message": "Missing token"}), 401

        is_valid, error_message = jwt_service.is_token_valid(token, "access")
        if not is_valid:
            return jsonify({"error": "Unauthorized", "message": error_message}), 401
