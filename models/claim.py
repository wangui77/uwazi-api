from datetime import datetime

from services.db_service import db


class Claim(db.Model):
    __tablename__ = "claims"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Claim Identification
    claim_reference = db.Column(db.String(50), nullable=False, index=True)
    invoice_number = db.Column(
        db.String(50), unique=True, nullable=False, index=True)
    policy_number = db.Column(db.String(50))

    # populated from the associated treatment cost
    invoice_amount = db.Column(db.Numeric(15, 2))

    # populated from the associated treatment cost
    min_cost = db.Column(db.Numeric(15, 2))
    maximum_cost = db.Column(db.Numeric(15, 2))

    # possible-under-reporting, within-limit, above-limit -> calculated based on min_cost and max_cost and invoice_amount
    risk_classification = db.Column(db.String(50))

    # comments on the claim info by the hospital
    claim_narration = db.Column(db.String(500))

    # Authorization
    # hospital admin user name
    created_by = db.Column(db.String(100))

    # insurance admin user name
    approved_by = db.Column(db.String(100))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_approved = db.Column(db.DateTime)

    # remarks on the approval by the insurance admin
    approval_remarks = db.Column(db.String(255))

    # Status
    # | Code    | Description
    # | ------- | -----------
    # | 00      | Pending
    # | 01      | Approved
    # | 02      | Rejected
    # | 03      | Disputed
    status_code = db.Column(db.String(50))
    status_description = db.Column(db.Text)

    # Relationships
    treatment_id = db.Column(
        db.Integer,
        db.ForeignKey('treatments.id', ondelete='CASCADE'),
        nullable=False
    )

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
