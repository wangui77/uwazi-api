import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from models.claim import Claim
from models.organisation import Organisation
from models.policy import Policy
from models.role import Role
from models.treatment import Treatment
from models.treatment_cost import TreatmentCost
from models.user import User
from services.db_service import db
from services.jwt_service import jwt_service
from utils.auth import generate_strong_password
from utils.email import send_password_email


class InsuranceService:
    def __init__(self):
        self.valid_status_codes = {
            "00": "Pending",
            "01": "Approved",
            "02": "Rejected",
            "03": "Disputed",
        }
        self.required_claims_fields = [
            "invoice_number",
            "invoice_amount",
            "treatment_id",
            "customer_id",
            "hospital_id",
            "insured_id"
        ]

    def derive_status_code_and_description(self, status_text):
        # Normalize the input status text to match case-insensitively
        status_text_lower = status_text.lower()

        # Find the matching status_code and status_description
        for code, description in self.valid_status_codes.items():
            if description.lower() == status_text_lower:
                return code, description

        # Return None if the status is invalid
        return None, None

    # ==================================
    #
    #  Policy
    #
    # =================================
    def can_pre_authorise_claims(self, token):
        claims = jwt_service.decode_identity(token)
        organisation = Organisation.query.get(claims["org_id"])
        role = Role.query.get(claims["role_id"])
        user = User.query.get(claims["id"])

        if not organisation or organisation.type != "hospital":
            return False, {"error": "You must belong to a hospital organisation to create a claim"}

        if not role or role.role_code != "admin":
            return False, {"error": "You must be an admin to create a claim"}

        return True, {"user_name": user.user_name, "org_id": organisation.id, "hospital_category": organisation.hospital_category}

    def get_policy_details(self, customer_id):

        # validate that the customer_id is a valid user
        user = User.query.get(customer_id)
        if not user:
            return {"error": "Customer does not exist"}, 404

        # Validate that the customer is an insurance customer
        customer_role_id = user.role_id
        customer_org_id = user.org_id
        user_role_code = Role.query.get(customer_role_id).role_code
        customer_organisation = Organisation.query.get(customer_org_id)
        customer_organisation_type = customer_organisation.type
        customer_is_active = user.status_code == "01"

        if not customer_organisation:
            return False, {"error": "Customers insurer organisation does not exist"}, 404

        if not customer_organisation_type == "insurance":
            return False, {"error": "Customer is not registered under an insurer"}, 400

        if not user_role_code == "user":
            return False, {"error": "Customer is not an insurance customer"}, 400

        if not customer_is_active:
            return False, {"error": "Customer is not active"}, 400

        # Get the user policy
        policy = Policy.query.filter_by(user_id=customer_id).first()
        if not policy:
            return False, {"error": "Customer does not have a policy"}, 404

        # Check if the policy is expired
        policy_end_date = policy.policy_end_date
        is_expired = policy_end_date < datetime.utcnow().date()
        if is_expired:
            return False, {"error": "Customers insurance Policy is expired"}, 400

        # Return the policy details
        response = {
            "policy_number": policy.policy_number,
            "premium_amount": policy.premium_amount,
            "policy_start_date": policy.policy_start_date,
            "policy_end_date": policy.policy_end_date,
            "remaining_limit": policy.remaining_limit,
            "insurer_name": customer_organisation.name,
            "is_expired": is_expired,

        }

        return True, response, 200

    def pre_authorisation(self, request):
        # Extract data from the request
        data = request.get_json()
        customer_id = data.get("customer_id")

        if not customer_id:
            return {"error": "Missing customer_id"}, 400

        # Ensure the user is logged in
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        can_pre_authorise_claims, user_data = self.can_pre_authorise_claims(
            token)
        if not can_pre_authorise_claims:
            return {'error': 'Only a hospital admin can pre-authorise claims'}, 401

        # get the policy details
        _is_valid, response, status_code = self.get_policy_details(customer_id)

        return response, status_code

    def get_policy_usage(self, request):
        # Ensure the user is logged in
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        claims = jwt_service.decode_identity(token)
        customer = User.query.get(claims["id"])
        if not customer.id:
            return {"error": "Missing customer_id"}, 400

        # get the policy details
        _is_valid, response, status_code = self.get_policy_details(customer.id)

        return response, status_code

    # ==================================
    #
    #  Claims
    #
    # =================================

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

    def can_fetch_or_update_claims(self, token):
        """Check if the user is an admin of a hospital organisation."""
        claims = jwt_service.decode_identity(token)
        organisation = Organisation.query.get(claims["org_id"])
        role = Role.query.get(claims["role_id"])
        user = User.query.get(claims["id"])
        role_code = role.role_code

        # organisation type should be insurance or hospital
        # role code should be admin or user
        if not organisation or organisation.type not in ["insurance", "hospital"]:
            return False, {"error": "You must belong to a hospital organisation to create a claim"}

        if not role or role.role_code not in ["admin", "user"]:
            return False, {"error": "You must be an admin or user to fetch or update a claim"}

        return True, {
            "user_name": user.user_name,
            "user_id": user.id,
            "org_id": organisation.id,
            "org_name": organisation.name,
            "org_type": organisation.type,
            "role_code": role_code,
        }

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

        # Extract data from request
        data = request.json

        invoice_number = data.get("invoice_number")
        invoice_amount = data.get("invoice_amount")
        treatment_id = data.get("treatment_id")
        customer_id = data.get("customer_id")
        hospital_id = data.get("hospital_id")
        insured_id = data.get("insured_id")
        claim_narration = data.get("claim_narration", "")

        # Validate required fields
        missing_fields = [
            field for field in self.required_claims_fields if data.get(field) in [None]
        ]

        print(f"Missing fields: {missing_fields}", flush=True)
        if missing_fields:
            return {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        if not invoice_number:
            return {"error": "Missing invoice_number"}, 400
        if not invoice_amount:
            return {"error": "Missing invoice_amount"}, 400
        if not customer_id:
            return {"error": "Missing customer_id"}, 400
        if not hospital_id:
            return {"error": "Missing hospital_id"}, 400
        if not insured_id:
            return {"error": "Missing insured_id"}, 400

        # Validate that the user exists
        user = User.query.get(customer_id)
        if not user:
            return {"error": f"User with ID '{customer_id}' not found"}, 404

        # validate the users policy details
        is_valid, policy_details_or_error, status_code = self.get_policy_details(
            customer_id)
        if not is_valid:
            return policy_details_or_error, status_code

        # Validate that the user can afford to pay the claim from their insurance
        remaining_limit = policy_details_or_error["remaining_limit"]
        if invoice_amount > remaining_limit:
            return {"error": "Insufficient funds to pay the claim"}, 400

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
            policy = Policy.query.filter_by(user_id=customer_id).first()
            if not policy:
                return {"error": "No policy found for the user"}, 404

            policy_number = policy.policy_number

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

        # Verify that the user is authorized to view claims. He must be an insurance admin
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        can_fetch_or_update_claims, user_data = self.can_fetch_or_update_claims(
            token)
        if not can_fetch_or_update_claims:
            return user_data, 401

        # Fetch claims
        # Use .all() to get the list
        # if the user is an insurance admin, fetch all claims
        # if the user is an insurance customer fetch only their claims
        # if the user is a hospital admin, fetch only claims for their hospital
        is_insurance_admin = user_data["role_code"] == "admin" and user_data["org_type"] == "insurance"
        is_insurance_customer = user_data["role_code"] == "user" and user_data["org_type"] == "insurance"
        is_hospital_admin = user_data["role_code"] == "admin" and user_data["org_type"] == "hospital"

        if not is_insurance_admin and not is_insurance_customer and not is_hospital_admin:
            return {"error": "Unauthorized", "message": "You are not authorized to view claims"}, 401

        claims = None

        if is_insurance_admin:
            claims = Claim.query.all()

        if is_insurance_customer:
            policy_number = Policy.query.filter_by(
                user_id=user_data["user_id"]).first().policy_number

            claims = Claim.query.filter_by(
                insured_id=user_data["org_id"], policy_number=policy_number).all()

        if is_hospital_admin:
            claims = Claim.query.filter_by(
                hospital_id=user_data["org_id"]).all()

        # Manually serialize claims
        if claims:
            claims_list = []
            for claim in claims:
                hospital_name = Organisation.query.get(claim.hospital_id).name
                insurer_name = Organisation.query.get(claim.insured_id).name

                claims_list.append({
                    "claim_id": claim.id,
                    "claim_reference": claim.claim_reference,
                    "invoice_number": claim.invoice_number,
                    "policy_number": claim.policy_number,
                    "invoice_amount": claim.invoice_amount,
                    "min_cost": claim.min_cost,
                    "maximum_cost": claim.maximum_cost,
                    "risk_classification": claim.risk_classification,
                    "claim_narration": claim.claim_narration,
                    "date_created": claim.date_created.isoformat() if claim.date_created else None,
                    "date_approved": claim.date_approved.isoformat() if claim.date_approved else None,
                    "approval_remarks": claim.approval_remarks,
                    "status_code": claim.status_code,
                    "status_description": claim.status_description,
                    "treatment_id": claim.treatment_id,
                    "hospital_id": claim.hospital_id,
                    "hospital_name": hospital_name,
                })
            return claims_list, 200
        else:
            return {"error": "No claims found"}, 404

    def update_claim(self, request):

        # Extract data from the request
        data = request.get_json()
        claim_id = data.get("claim_id")
        # status can be approved, rejected or disputed
        status = data.get("status")
        remarks = data.get("remarks")
        insurer_id = data.get("insurer_id")
        org_id = int(insurer_id)

        # Verify that the user is authorized to update claims
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        # verify the organisation exists
        organisation = Organisation.query.get(org_id)
        if not organisation:
            return {"error": "Invalid organisation"}, 400

        can_fetch_or_update_claims, user_data = self.can_fetch_or_update_claims(
            token)
        if not can_fetch_or_update_claims:
            return user_data, 401

        # validate the status
        if status not in ["approved", "rejected", "disputed"]:
            return {"error": "Invalid status"}, 400

        # Fetch the claim
        claim = Claim.query.get(claim_id)
        if not claim:
            return {"error": "Claim not found"}, 404

        # Update the claim status
        status_code, status_description = self.derive_status_code_and_description(
            status)

        claim.status_code = status_code
        claim.status_description = status_description
        claim.approval_remarks = remarks

        if status == "approved":
            claim.date_approved = datetime.utcnow()
            claim.approved_by = user_data["user_name"]

            # reduce the users limit
            policy = Policy.query.filter_by(
                policy_number=claim.policy_number).first()

            policy.remaining_limit -= claim.invoice_amount

        # Save the changes to the database
        try:
            db.session.commit()

            return {
                "message": "Claim updated successfully",
                "claim_id": claim.id,
                "claim_reference": claim.claim_reference,
                "invoice_number": claim.invoice_number,
                "policy_number": claim.policy_number,
                "invoice_amount": claim.invoice_amount,
            }, 200

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback transaction on error
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while saving the claim. Please try again later."}, 500


insurance_service = InsuranceService()
