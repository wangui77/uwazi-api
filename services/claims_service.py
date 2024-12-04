import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from models.claim import Claim
from models.organisation import Organisation
from models.role import Role
from models.treatment import Treatment
from models.treatment_cost import TreatmentCost
from models.user import User
from services.db_service import db
from services.jwt_service import jwt_service
from utils.auth import generate_strong_password
from utils.email import send_password_email


class ClaimsService:
    def __init__(self):
        self.valid_status_codes = {
            "00": "Pending",
            "01": "Approved",
            "02": "Rejected",
            "03": "Disputed",
        }

    def can_create_claim(self, token):
        """Check if the user is an admin of a hospital organisation."""
        claims = jwt_service.decode_identity(token)
        organisation = Organisation.query.get(claims["org_id"])
        role = Role.query.get(claims["role_id"])
        user = User.query.get(claims["id"])

        if not organisation or organisation.type != "hospital":
            return False, {"error": "You must belong to a hospital organisation to create a claim"}

        if not role or role.role_code != "admin":
            return False, {"error": "You must be an admin to create a claim"}

        return True, {"user_name": user.user_name, "org_id": organisation.id, "hospital_category": organisation.hospital_category}

    def get_risk_classification(self, invoice_amount, min_cost, max_cost):
        """Calculate the risk classification based on invoice amount."""
        if invoice_amount < min_cost:
            return "possible-under-reporting"
        elif min_cost <= invoice_amount <= max_cost:
            return "within-limit"
        else:
            return "above-limit"

    def create_claim(self, request):
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        # Validate user permissions
        can_create_claim, user_data = self.can_create_claim(token)
        if not can_create_claim:
            return user_data, 401

        data = request.json
        invoice_number = data.get("invoice_number")
        policy_number = data.get("policy_number")
        invoice_amount = data.get("invoice_amount")
        treatment_id = data.get("treatment_id")
        hospital_id = data.get("hospital_id")
        insured_id = data.get("insured_id")
        claim_narration = data.get("claim_narration", "")

        # Validate required fields
        if not (invoice_number and policy_number and invoice_amount and treatment_id and hospital_id and insured_id):
            return {"error": "Missing required fields: invoice_number, policy_number, invoice_amount, treatment_id, hospital_id, insured_id"}, 400

        # Check if the claim already exists
        existing_claim = Claim.query.filter_by(
            invoice_number=invoice_number).first()
        if existing_claim:
            return {"error": f"Claim with invoice number '{invoice_number}' already exists"}, 409

        try:
            # Fetch treatment
            treatment = Treatment.query.get(treatment_id)
            if not treatment:
                return {"error": f"Treatment with ID '{treatment_id}' not found"}, 404

            # Fetch treatment cost based on hospital category
            treatment_cost = TreatmentCost.query.filter_by(
                treatment_id=treatment_id,
                hospital_category=user_data["hospital_category"]
            ).first()
            if not treatment_cost:
                return {"error": f"No treatment cost found for treatment ID '{treatment_id}' and hospital category '{user_data['hospital_category']}'"}, 404

            # Extract min and max costs
            min_cost = treatment_cost.min_cost
            max_cost = treatment_cost.maximum_cost

            # Determine risk classification
            risk_classification = self.get_risk_classification(
                invoice_amount, min_cost, max_cost)

            # Create the claim
            claim = Claim(
                claim_reference=str(uuid.uuid4()),
                invoice_number=invoice_number,
                policy_number=policy_number,
                invoice_amount=invoice_amount,
                treatment_id=treatment_id,
                min_cost=min_cost,
                maximum_cost=max_cost,
                risk_classification=risk_classification,
                claim_narration=claim_narration,
                created_by=user_data["user_name"],
                hospital_id=hospital_id,
                insured_id=insured_id,
                status_code="00",
                status_description=self.valid_status_codes["00"],
                date_created=datetime.utcnow(),
            )

            db.session.add(claim)
            db.session.commit()

            return {
                "message": "Claim created successfully",
                "data": {
                    "id": claim.id,
                    "claim_reference": claim.claim_reference,
                    "invoice_number": claim.invoice_number,
                    "policy_number": claim.policy_number,
                    "invoice_amount": claim.invoice_amount,
                    "min_cost": claim.min_cost,
                    "maximum_cost": claim.maximum_cost,
                    "risk_classification": claim.risk_classification,
                    "claim_narration": claim.claim_narration,
                    "created_by": claim.created_by,
                    "status_code": claim.status_code,
                    "status_description": claim.status_description,
                    "date_created": claim.date_created,
                },
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback transaction on error
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while saving the claim. Please try again later."}, 500

    def get_claims(self, request):
        return {"message": "claims will go here"}, 200


claims_service = ClaimsService()
