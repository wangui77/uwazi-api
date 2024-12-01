from datetime import datetime

from app.services.db_service import db


class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(500))

    # Authorization
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)

    # Status
    status_code = db.Column(db.String(50))
    status_description = db.Column(db.Text)

    # Relationships
    costs = db.relationship(
        "TreatmentCost",
        backref="treatment",
        lazy=True,
        cascade="all, delete-orphan",
    )