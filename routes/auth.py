from flask import jsonify, request
from flask_jwt_extended import (jwt_required, set_access_cookies,
                                set_refresh_cookies)
from services.jwt_service import jwt_service


def register_auth_routes(app):
    @app.route("/auth/login", methods=["POST"])
    def login():
        from services.user_service import user_service

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

    @app.route("/auth/logout", methods=["POST"])
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

    @app.route("/auth/refresh", methods=["POST"])
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

    @app.route("/auth/register", methods=["POST"])
    def register():
        '''
            - We need to seed the database with the default user
            - The default user can then create other users if they are a super admin
            - The default user can also create other super admins if they are a super admin
            - The default user can change their password if they are a super admin
        '''
        response = jsonify({"error": "Registration route not implemented"})

        return response, 500
