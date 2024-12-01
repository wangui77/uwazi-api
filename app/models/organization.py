from datetime import datetime

from app.services.db_service import db


class Organisation(db.Model):
    __tablename__ = 'organisations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Organization Details
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # "hospital", "insurance", or "provider"

    # Tax
    kra_pin = db.Column(db.String(50))
    
    #  Location
    head_quarter_location = db.Column(db.String(255))

    # Contact Details
    email_address = db.Column(db.String(255), unique=True)
    mobile_number = db.Column(db.String(20))

    # Hospital-specific field
    hospital_category = db.Column(db.String(50))  # Applies only to hospitals, i.e., "public", "private"

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Authorization
    created_by = db.Column(db.String(100))
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)

    # Status
    status_code = db.Column(db.String(50), nullable=True)
    status_description = db.Column(db.Text, nullable=True)

    # Relationships
    users = db.relationship('User', backref='organisation', lazy=True, cascade='all, delete-orphan')
