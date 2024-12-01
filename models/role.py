from datetime import datetime

from services.db_service import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    role_code = db.Column(db.String(50), nullable=False)
    role_description = db.Column(db.String(255))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)