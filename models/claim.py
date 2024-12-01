from datetime import datetime

from services.db_service import db


class Claim(db.Model):
    __tablename__ = "claims"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Claim Identification
    claim_reference = db.Column(db.String(50), nullable=False, index=True)
    invoice_number = db.Column(db.String(50), nullable=False, index=True)
    policy_number = db.Column(db.String(50))

    # Procedure Details
    procedure_code = db.Column(db.String(50))
    invoice_amount = db.Column(db.Numeric(15, 2))
    min_cost = db.Column(db.Numeric(15, 2))
    maximum_cost = db.Column(db.Numeric(15, 2))
    risk_classification = db.Column(db.String(50))
    claim_narration = db.Column(db.String(500))

    # Authorization
    created_by = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100))
    date_approved = db.Column(db.DateTime)
    approval_remarks = db.Column(db.String(255))

    # Status
    status_code = db.Column(db.String(50))
    status_description = db.Column(db.Text)

    # Relationships
    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )
    insured_id = db.Column(
        db.Integer,
        db.ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Bidirectional Relationships
    hospital = db.relationship(
        "Organisation",
        foreign_keys=[hospital_id],
        back_populates="claims_as_hospital",
        lazy=True,
    )

    insurer = db.relationship(
        "Organisation",
        foreign_keys=[insured_id],
        back_populates="claims_as_insurer",
        lazy=True,
    )
