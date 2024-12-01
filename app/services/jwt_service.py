import os
from datetime import datetime, timedelta

from app.models.token import Token
from app.services.db_service import db
from cryptography.fernet import Fernet
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                decode_token, get_jwt_identity)

# Ideally, fetch this from environment variables
ENCRYPTION_KEY = os.getenv(
    "SECRET_KEY", "9VV69kGgnBQkt23Rn8Gx2oweiutxFo4prbVY-EbSt8Q=")
cipher = Fernet(ENCRYPTION_KEY)


class JWTService:
    def encrypt_token(self, token):
        return cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, token):
        return cipher.decrypt(token.encode()).decode()

    def generate_tokens(self, identity):
        access_token = create_access_token(
            identity=identity, expires_delta=timedelta(minutes=15))
        refresh_token = create_refresh_token(
            identity=identity, expires_delta=timedelta(days=7))
        return access_token, refresh_token

    def store_token(self, user_id, token, token_type, expires_in_minutes):
        encrypted_token = self.encrypt_token(token)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        new_token = Token(
            user_id=user_id, token=encrypted_token, token_type=token_type, expires_at=expires_at, revoked=False
        )
        db.session.add(new_token)
        db.session.commit()

    def revoke_token(self, token):
        encrypted_token = self.encrypt_token(token)
        token_entry = Token.query.filter_by(token=encrypted_token).first()
        if token_entry:
            token_entry.revoked = True
            db.session.commit()

    def is_token_valid(self, token, token_type):
        encrypted_token = self.encrypt_token(token)
        token_entry = Token.query.filter_by(
            token=encrypted_token, token_type=token_type).first()
        if not token_entry:
            return False, "Token not found"
        if token_entry.revoked:
            return False, "Token has been revoked"
        if token_entry.expires_at < datetime.utcnow():
            return False, "Token has expired"

        if token_entry.expires_at < datetime.utcnow():
            # Remove expired tokens during validation
            db.session.delete(token_entry)
            db.session.commit()
            return False, "Token has expired"
        return True, None

    def cleanup_expired_tokens(self):
        expired_tokens = Token.query.filter(
            Token.expires_at < datetime.utcnow()).all()
        for token in expired_tokens:
            db.session.delete(token)
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

    def get_identity(self):
        """
        Extract the identity from the current JWT token.
        """
        return get_jwt_identity()


jwt_service = JWTService()
