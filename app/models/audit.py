from datetime import datetime

from app.services.db_service import db


class AuditTrail(db.Model):
    __tablename__ = "audit_trail"

    id = db.Column(db.BigInteger, primary_key=True)
    log_ref = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(50))
    active_page = db.Column(db.String(255))
    activity_done = db.Column(db.String(255))
    system_module = db.Column(db.String(100))
    audit_date = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))