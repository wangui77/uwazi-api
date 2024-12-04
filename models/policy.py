from datetime import datetime

from services.db_service import db


class Policy(db.Model):
    __tablename__ = 'policies'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Policy
    policy_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    policy_start_date = db.Column(
        db.Date, nullable=False, default=datetime.utcnow)  # Start date of the policy

    policy_end_date = db.Column(
        db.Date, nullable=False)  # End date of the policy

    premium_amount = db.Column(db.Numeric(
        15, 2), nullable=False)  # Premium payment amount

    remaining_limit = db.Column(db.Numeric(15, 2), nullable=False)

    # Relationships
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Timestamps
    # Auto-filled on creation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)  # Auto-updated on modification
