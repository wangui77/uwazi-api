import json
import os
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                decode_token, get_jwt_identity,
                                verify_jwt_in_request)

from models.token import Token
from services.db_service import db

# Ideally, fetch this from environment variables
ENCRYPTION_KEY = os.getenv(
    "SECRET_KEY", "9VV69kGgnBQkt23Rn8Gx2oweiutxFo4prbVY-EbSt8Q=")
cipher = Fernet(ENCRYPTION_KEY)


class JWTService:

    # Helpers
    def encrypt_token(self, token):
        return cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, token):
        return cipher.decrypt(token.encode()).decode()

    def get_token_from_request(self, request):
        token = None
        if "Authorization" in request.headers and request.headers["Authorization"].startswith("Bearer "):
            token = request.headers["Authorization"].split(" ")[1]
        elif "access_token" in request.cookies:
            token = request.cookies.get("access_token")

        print(f"Token from request: {token}", flush=True)

        return token

    # Generation and storage
    def generate_tokens(self, identity):
        identity_string = json.dumps(identity)

        access_token = create_access_token(
            identity=identity_string, expires_delta=timedelta(minutes=15)
        )
        refresh_token = create_refresh_token(
            identity=identity_string, expires_delta=timedelta(days=7)
        )

        return access_token, refresh_token

    def store_token(self, user_id, token, token_type, expires_in_minutes):
        encrypted_token = self.encrypt_token(token)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        new_token = Token(
            user_id=user_id, token=encrypted_token, token_type=token_type, expires_at=expires_at, revoked=False
        )
        db.session.add(new_token)
        db.session.commit()

    def replace_refresh_token(self, user_id, new_refresh_token):
        encrypted_new_token = self.encrypt_token(new_refresh_token)
        Token.query.filter_by(user_id=user_id, token_type="refresh").delete()
        expires_at = datetime.utcnow() + timedelta(days=7)
        new_token = Token(
            user_id=user_id, token=encrypted_new_token, token_type="refresh", expires_at=expires_at, revoked=False
        )
        db.session.add(new_token)
        db.session.commit()

    # Revocation and Cleanup
    def revoke_token(self, token):
        # Decode the token to get the claims
        decoded_claims = self.decode_identity(token)

        if not decoded_claims:
            return False

        user_id = decoded_claims["id"]

        access_token_entry = Token.query.filter_by(
            token_type="access",
            user_id=user_id
        ).first()

        refresh_token_entry = Token.query.filter_by(
            token_type="refresh",
            user_id=user_id
        ).first()

        if access_token_entry:
            access_token_entry.revoked = True

        if refresh_token_entry:
            refresh_token_entry.revoked = True

        db.session.commit()

        return True

    def revoke_all_user_tokens(self, user_id):
        tokens = Token.query.filter_by(user_id=user_id).all()
        for token in tokens:
            token.revoked = True
        db.session.commit()

    def clear_revoked_tokens(self):
        revoked_tokens = Token.query.filter_by(revoked=True).all()
        for token in revoked_tokens:
            db.session.delete(token)
        db.session.commit()

    def cleanup_expired_tokens(self):
        expired_tokens = Token.query.filter(
            Token.expires_at < datetime.utcnow()).all()
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()

    # Validation
    def is_token_valid(self, token, token_type):
        # Decode the token to get the claims
        decoded_claims = self.decode_identity(token)

        if not decoded_claims:
            return False, "Token expired or invalid"

        print(f"decoded_claims: {decoded_claims}")

        user_id = decoded_claims["id"]

        # Verify the token
        token_entry = Token.query.filter_by(
            token_type=token_type,
            user_id=user_id
        ).first()

        if not token_entry:
            return False, "Token does not exist"

        # Decrypt the saved token
        saved_token = self.decrypt_token(token_entry.token)

        if saved_token != token:
            return False, "Token mismatch"

        if token_entry.revoked:
            return False, "Token has been revoked"

        if token_entry.expires_at < datetime.utcnow():
            db.session.delete(token_entry)
            db.session.commit()
            return False, "Token has expired"

        return True, None

    def decode_identity(self, token):
        """
        Decode the token and retrieve the original identity dictionary,
        while verifying the token's validity.
        """
        try:
            # Verify the token (validates signature and claims)
            verify_jwt_in_request()

            # Decode the token
            decoded_token = decode_token(token)
            identity_string = decoded_token["sub"]
            identity = json.loads(identity_string)

            return identity
        except Exception as e:
            print(token, flush=True)
            print(f"Error decoding token: {e}", flush=True)
            # Handle token verification or decoding errors
            return None

    def get_identity(self):
        """
        Extract the identity from the current JWT token.
        """
        return get_jwt_identity()


jwt_service = JWTService()
