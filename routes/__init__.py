from flask import jsonify, request
from flask_jwt_extended import set_access_cookies, set_refresh_cookies

from services.claims_service import claims_service
from services.jwt_service import jwt_service
from services.registration_service import registration_service
from services.treatment_service import treatment_service
from utils.routes import create_route_with_prefix


def general_routes(app):
    # Health check endpoint
    from utils.routes import create_route_with_prefix

    @app.route(create_route_with_prefix("/health"), methods=["GET"])
    def health():
        return {"status": "healthy"}, 200


def auth_routes(app):
    @app.route(create_route_with_prefix("/auth/login"), methods=["POST"])
    def login():
        from services.user_service import user_service

        user = user_service.verify_user(request.json)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        # set all previous tokens to revoked and clear all revoked tokens
        jwt_service.revoke_all_user_tokens(user.id)
        jwt_service.clear_revoked_tokens()

        # Generate new tokens
        identity_claims = {
            "id": user.id,
            "user_name": user.user_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "org_id": user.org_id,
            "role_id": user.role_id
        }

        access_token, refresh_token = jwt_service.generate_tokens(
            identity_claims)

        # Store the new tokens in the database
        jwt_service.store_token(
            user.id,
            access_token,
            "access", expires_in_minutes=15
        )
        jwt_service.store_token(
            user.id, refresh_token,
            "refresh",
            expires_in_minutes=7 * 24 * 60
        )

        # Set the tokens in the response cookies and response body
        response = jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        })

        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response, 200

    @app.route(create_route_with_prefix("/auth/logout"), methods=["POST"])
    def logout():
        # Get the JWT from the Authorization header or cookie
        token = jwt_service.get_token_from_request(request)
        if not token:
            return jsonify({"error": "Unauthorized", "message": "Missing token"}), 401

        # Revoke the current token and clear all revoked tokens
        revoked = jwt_service.revoke_token(token)
        if not revoked:
            return jsonify({"error": "Failed to revoke token"}), 500

        # Clear all revoked tokens
        jwt_service.clear_revoked_tokens()
        jwt_service.cleanup_expired_tokens()

        # Clear the cookies and return the response
        response = jsonify({"message": "Logged out successfully"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response, 200

    @app.route(create_route_with_prefix("/auth/refresh"), methods=["POST"])
    def refresh_token():
        identity = jwt_service.get_identity()
        access_token, refresh_token = jwt_service.generate_tokens(identity)

        jwt_service.store_token(
            identity["user_id"], access_token, "access", expires_in_minutes=15)
        jwt_service.replace_refresh_token(identity["user_id"], refresh_token)

        response = jsonify({"message": "Token refreshed",
                            "access_token": access_token})
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 200

    @app.route(create_route_with_prefix("/auth/register/<registration_type>"), methods=["POST"])
    def register(registration_type):
        registration_type = registration_type.lower()

        if registration_type == "organisation":
            response, response_code = registration_service.register_organisation(
                request)
        elif registration_type == "user":
            response, response_code = registration_service.register_user(
                request)
        else:
            return jsonify({"error": f"Invalid registration type: {registration_type}"}), 400

        return jsonify(response), response_code


def treatment_routes(app):
    @app.route(create_route_with_prefix("/treatment"), methods=["POST"])
    def treatment():
        response, response_code = treatment_service.create_treatment_with_costs(
            request)
        return response, response_code


def claims_routes(app):
    @app.route(create_route_with_prefix("/claims"), methods=["POST"])
    def claim():
        response, response_code = claims_service.create_claim(
            request)
        return response, response_code
    
    @app.route(create_route_with_prefix("/claims"), methods=["GET"])
    def get_claims():
        response, response_code = claims_service.get_claims(
            request)
        return response, response_code


def register_routes(app):
    auth_routes(app)
    general_routes(app)
    claims_routes(app)
    treatment_routes(app)
