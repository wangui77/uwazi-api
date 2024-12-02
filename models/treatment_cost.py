from datetime import datetime

from services.db_service import db


class TreatmentCost(db.Model):
    __tablename__ = "treatment_costs"

    id = db.Column(db.Integer, primary_key=True)
    # e.g., "public", "private"
    hospital_category = db.Column(db.String(50), nullable=False)

    # Costs
    min_cost = db.Column(db.Numeric(15, 2), nullable=False)
    maximum_cost = db.Column(db.Numeric(15, 2), nullable=False)

    # Authorization
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)

    # Timestamps
    updated_by = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime)

    # Status
    status_code = db.Column(db.String(50))
    status_description = db.Column(db.Text)

    # Relationships
    treatment_id = db.Column(db.Integer, db.ForeignKey(
        "treatments.id"), nullable=False)  # Foreign key to Treatment
