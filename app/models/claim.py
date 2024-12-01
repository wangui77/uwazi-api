from datetime import datetime

from app.services.db_service import db


class Claim(db.Model):
    __tablename__ = "claims"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Claim Identification
    claim_reference = db.Column(db.String(50), nullable=False, index=True)  # Unique identifier for the claim
    invoice_number = db.Column(db.String(50), nullable=False, index=True)  # Invoice associated with the claim
    policy_number = db.Column(db.String(50))  # Policy number linked to the claim


    # Procedure Details
    procedure_code = db.Column(db.String(50))  # Code identifying the procedure
    invoice_amount = db.Column(db.Numeric(15, 2))  # Amount charged on the invoice
    min_cost = db.Column(db.Numeric(15, 2))  # Minimum allowable cost for the procedure
    maximum_cost = db.Column(db.Numeric(15, 2))  # Maximum allowable cost for the procedure
    risk_classification = db.Column(db.String(50))  # Risk classification for the claim (e.g., low/high risk)
    claim_narration = db.Column(db.String(500))  # Detailed explanation of the claim

    # Authorization
    created_by = db.Column(db.String(100))  # User who created the claim
    date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp for when the claim was created
    approved_by = db.Column(db.String(100))  # User who approved the claim
    date_approved = db.Column(db.DateTime)  # Timestamp for when the claim was approved
    approval_remarks = db.Column(db.String(255))  # Remarks provided during approval

    # Status
    status_code = db.Column(db.String(50))  # Status code (e.g., pending/approved/rejected)
    status_description = db.Column(db.Text)  # Description of the claim's status


    # Relationships
    hospital_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)  # Foreign key to hospital
    insured_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)  # Foreign key to insurer
    
    
    # Relationship to fetch hospital details
    hospital = db.relationship(
        "Organization", 
        foreign_keys=[hospital_id], 
        lazy=True
        )  
    
    # Relationship to fetch insurer details
    insurer = db.relationship(
        "Organization", 
        foreign_keys=[insured_id], 
        lazy=True
    ) 
