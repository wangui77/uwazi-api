import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from models.organisation import Organisation
from models.role import Role
from models.treatment import Treatment
from models.treatment_cost import TreatmentCost
from models.user import User
from services.db_service import db
from services.jwt_service import jwt_service
from utils.auth import generate_strong_password
from utils.email import send_password_email


class TreatmentService:
    def __init__(self):
        self.required_treatment_fields = [
            "name",
            "type",
            "email_address",
            "mobile_number",
            "head_quarter_location",
            "kra_pin"
        ]
        self.required_user_fields = [
            "user_name",
            "first_name",
            "last_name",
            "email",
            "org_id",
            "national_id",
            "gender",
            "dob",
            "mobile_number",
        ]
        self.valid_org_types = ["hospital", "insurance"]
        self.valid_hospital_categories = ["public", "private"]

    # Permission Checkers
    def can_create_treatment_procedure(self, token):
        """Validate that the user is a super admin from the provider organisation."""
        claims = jwt_service.decode_identity(token)
        organisation = Organisation.query.get(claims["org_id"])
        role = Role.query.get(claims["role_id"])
        user = User.query.get(claims["id"])

        if not organisation or organisation.type != "provider":
            return False, {"error": "You are not authorized to add an treatment procedure"}

        if not role or role.role_code != "super_admin":
            return False, {"error": "You are not authorized to add an treatment procedure"}

        return True, {"user_name": user.user_name}

    # Helper functions
    def get_admin_claims_from_token(self, token):
        """Validate that the user is a super admin from the provider organisation."""
        claims = jwt_service.decode_identity(token)
        organisation = self.get_organisation(claims["org_id"])
        role = Role.query.get(claims["role_id"])

        if role and role.role_code == "super_admin" and organisation.type == "provider":
            return "super_admin", claims
        elif role and role.role_code == "admin" and organisation.type != "provider":
            return "admin", claims
        else:
            return None, None

    # Validation functions
    def validate_treatments_payload(self, data):
        # missing_fields = [
        #     field for field in self.required_org_fields if not data.get(field)]
        # if missing_fields:
        #     return False, {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        # org_type = data["type"].lower()
        # if org_type not in self.valid_org_types:
        #     return False, {"error": f"Invalid organization type: {org_type}"}, 400

        # if org_type == "hospital":
        #     hospital_category = data.get("hospital_category")
        #     if hospital_category not in self.valid_hospital_categories:
        #         return False, {
        #             "error": "hospital_category must be 'public', 'private', or None"
        #         }, 400

        # return True, None
        return True, None

    # Treatment procedures handlers
    def create_treatment_with_costs(self, request):
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        # Validate super admin
        can_create_treatment_procedure, admin_data = self.can_create_treatment_procedure(
            token)
        if not can_create_treatment_procedure:
            return admin_data, 401

        # Validate request payload
        data = request.json
        treatment_name = data.get("name")
        description = data.get("description", "")
        cost_data = data.get("costs", [])

        if not treatment_name or not cost_data:
            return {"error": "Missing required fields: 'name' or 'costs'"}, 400

        try:
            # Check if treatment already exists
            existing_treatment = Treatment.query.filter_by(
                name=treatment_name).first()

            if existing_treatment:
                treatment = existing_treatment
            else:
                # Create a new treatment
                unique_code = str(uuid.uuid4())
                treatment = Treatment(
                    name=treatment_name,
                    code=unique_code,
                    description=description,
                    created_by=admin_data["user_name"],
                    created_at=datetime.utcnow(),
                    approved_by=admin_data["user_name"],
                    status_code="01",
                    status_description="Active",
                )
                db.session.add(treatment)
                db.session.flush()  # Flush to get the treatment ID

            # Process treatment costs
            cost_errors = self.process_treatment_costs(
                treatment_id=treatment.id,
                cost_data=cost_data,
                created_by=admin_data["user_name"]
            )
            if cost_errors:
                return {"error": cost_errors}, 400

            db.session.commit()

            return {
                "message": "Treatment and associated costs created successfully",
                "data": {
                    "id": treatment.id,
                    "name": treatment.name,
                    "description": treatment.description,
                    "costs": [
                        {
                            "hospital_category": cost["hospital_category"],
                            "min_cost": cost["min_cost"],
                            "maximum_cost": cost["maximum_cost"],
                        }
                        for cost in cost_data
                    ],
                },
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback the transaction
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while saving the data. Please try again later."}, 500

    def process_treatment_costs(self, treatment_id, cost_data, created_by):
        errors = []

        for cost in cost_data:
            hospital_category = cost.get("hospital_category")
            min_cost = cost.get("min_cost")
            maximum_cost = cost.get("maximum_cost")

            # Validate cost data
            if hospital_category not in self.valid_hospital_categories or min_cost is None or maximum_cost is None:
                errors.append(f"Invalid cost data for {hospital_category}")
                continue

            # Check if cost already exists for the hospital category
            existing_cost = TreatmentCost.query.filter_by(
                treatment_id=treatment_id, hospital_category=hospital_category
            ).first()

            if existing_cost:
                errors.append(
                    f"Cost for hospital category '{hospital_category}' already exists.")
                continue

            # Add new treatment cost
            treatment_cost = TreatmentCost(
                treatment_id=treatment_id,
                hospital_category=hospital_category,
                min_cost=min_cost,
                maximum_cost=maximum_cost,
                created_by=created_by,
                created_at=datetime.utcnow(),
                approved_by=created_by,
                approved_at=datetime.utcnow(),
                status_code="01",
                status_description="Active",
            )
            db.session.add(treatment_cost)

        return errors if errors else None


treatment_service = TreatmentService()
