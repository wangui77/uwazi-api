from datetime import datetime

from services.db_service import db


class Organisation(db.Model):
    __tablename__ = 'organisations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Organization Details
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    # "hospital", "insurance", or "provider"
    type = db.Column(db.String(50), nullable=False)

    # Tax
    kra_pin = db.Column(db.String(50), nullable=True)

    # Location
    head_quarter_location = db.Column(db.String(255), nullable=True)

    # Contact Details
    email_address = db.Column(db.String(255), unique=True, nullable=True)
    mobile_number = db.Column(db.String(20), nullable=True)

    # Hospital-specific field
    # Applies only to hospitals, i.e., "public", "private"
    hospital_category = db.Column(db.String(50), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Authorization
    created_by = db.Column(db.String(100))
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Status
    status_code = db.Column(db.String(50), nullable=True)
    status_description = db.Column(db.Text, nullable=True)

    # Relationships
    users = db.relationship(
        'User', backref='organisation', lazy=True, cascade='all, delete-orphan'
    )

    claims_as_hospital = db.relationship(
        'Claim',
        foreign_keys='Claim.hospital_id',
        back_populates='hospital',
        lazy=True,
    )

    claims_as_insurer = db.relationship(
        'Claim',
        foreign_keys='Claim.insured_id',
        back_populates='insurer',
        lazy=True,
    )
