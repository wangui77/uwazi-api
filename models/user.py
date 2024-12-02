from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from services.db_service import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User PII
    user_name = db.Column(db.String(50), unique=True,
                          nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    second_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    national_id = db.Column(db.String(50), unique=True, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date)

    # User Contact Details
    mobile_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Security
    password_hash = db.Column(db.String(255), nullable=False)
    last_login_date = db.Column(db.DateTime)
    # Default login attempts to 0
    login_trials = db.Column(db.Integer, default=3)
    login_ip = db.Column(db.String(50))

    # Relationships
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    # Foreign Key to Organization which can be a hospital, insurance company or a provider
    org_id = db.Column(db.Integer, db.ForeignKey(
        'organisations.id'), nullable=False)

    # Authorization
    created_by = db.Column(db.String(100), nullable=False)
    approved_by = db.Column(db.String(100), default="system")
    approved_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Status
    status_code = db.Column(db.String(50), nullable=False, default="active")
    status_description = db.Column(db.Text)
