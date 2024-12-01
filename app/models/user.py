from datetime import datetime

from app.services.db_service import db
from werkzeug.security import check_password_hash, generate_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # User PII
    user_name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    second_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date)

    # User Contact Details
    mobile_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Security
    password_hash = db.Column(db.String(255), nullable=False)
    last_login_date = db.Column(db.DateTime)
    login_trials = db.Column(db.Integer, default=0)  # Default login attempts to 0
    login_ip = db.Column(db.String(50))

    # Relationships
    role_id = db.Column(db.String(50), db.ForeignKey("roles.id"), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False) # Foreign Key to Organization which can be a hospital, insurance company or a provider

    # Authorization
    created_by = db.Column(db.String(100), nullable=False)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Status
    status_code = db.Column(db.String(50), nullable=False, default="active")
    status_description = db.Column(db.Text)

    def set_password(self, password):
        """
        Hash and set the password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify the password against the hash.
        """
        return check_password_hash(self.password_hash, password)
