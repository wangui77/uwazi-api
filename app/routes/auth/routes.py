from app.routes import auth_bp
from app.services.jwt_service import jwt_service
from app.services.user_service import user_service
from flask import jsonify, request
from flask_jwt_extended import (jwt_required, set_access_cookies,
                                set_refresh_cookies)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # Validate input
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = user_service.verify_user(email, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    identity = {
        "user_id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "org_id": user.org_id,
    }

    access_token, refresh_token = jwt_service.generate_tokens(identity)

    jwt_service.store_token(user.id, access_token,
                            "access", expires_in_minutes=15)
    jwt_service.store_token(user.id, refresh_token,
                            "refresh", expires_in_minutes=7 * 24 * 60)

    response = jsonify({"message": "Login successful"})
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get("access_token")

    if not token:
        return jsonify({"error": "No token provided"}), 400

    # Revoke the current token
    jwt_service.revoke_token(token)

    # Clean up expired tokens
    jwt_service.cleanup_expired_tokens()

    response = jsonify({"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
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
