from datetime import datetime

from app.services.db_service import db


class Token(db.Model):
    __tablename__ = 'tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # FK to users table
    token = db.Column(db.Text, nullable=False)
    token_type = db.Column(db.String(20), nullable=False)  # "access" or "refresh"
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)