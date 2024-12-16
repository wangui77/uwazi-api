import uuid
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from models.organisation import Organisation
from models.policy import Policy
from models.role import Role
from models.user import User
from services.db_service import db
from services.jwt_service import jwt_service
from utils.auth import generate_policy_number, generate_strong_password
from utils.email import send_password_email


class RegistrationService:
    def __init__(self):
        self.required_org_fields = [
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
        self.required_insurance_customer_fields = [
            "premium_amount",
        ]
        self.valid_org_types = ["hospital", "insurance"]
        self.valid_hospital_categories = ["public", "private"]

    # Permission Checkers
    def can_create_organisation(self, token):
        """Validate that the user is a super admin from the provider organisation."""
        claims = jwt_service.decode_identity(token)
        organisation = Organisation.query.get(claims["org_id"])
        role = Role.query.get(claims["role_id"])
        user = User.query.get(claims["id"])

        if not organisation or organisation.type != "provider":
            return False, {"error": "You are not authorized to create an organisation"}

        if not role or role.role_code != "super_admin":
            return False, {"error": "You are not authorized to create an organisation"}

        return True, {"user_name": user.user_name}

    def can_create_user(self, request, data):
        # Validate admin permissions
        # Get admin details
        token = jwt_service.get_token_from_request(request)
        if not token:
            return False, {"error": "Unauthorized", "message": "Missing token"}, 401

        admin, admin_data = self.get_admin_claims_from_token(token)
        if not admin:
            return False, {"error": "Unauthorized"}, 401

        # Validate the organisation exists
        request_payload_org = Organisation.query.filter_by(
            id=data["org_id"]).first()
        if not request_payload_org:

            return False, {"error": f"Organisation with id {data['org_id']} not found"}, 404

        # only super admins can register other super admins
        if request_payload_org.type == "provider" and not admin == "super_admin":
            return False, {"error": "Only super admins can register other super admins"}, 403

        # admins can only register admins in their own organisation
        if request_payload_org.id != admin_data["org_id"] and admin == "admin":
            return False, {"error": "You can only register users in your own organisation"}, 403

        return True, admin_data, None

    def can_create_insurance_customer(self, request, data):
        # Validate admin permissions
        # Get admin details
        token = jwt_service.get_token_from_request(request)
        if not token:
            return False, {"error": "Unauthorized", "message": "Missing token"}, 401

        admin, admin_data = self.get_admin_claims_from_token(token)
        if not admin:
            return False, {"error": "Unauthorized"}, 401

        # Validate the organisation exists
        request_payload_org = Organisation.query.filter_by(
            id=data["org_id"]).first()
        if not request_payload_org:
            return False, {"error": f"Organisation with id {data['org_id']} not found"}, 404

        # only admins can register customers
        if request_payload_org.type == "insurance" and not admin == "admin":
            return False, {"error": "Only insurance admins can register insurance customers"}, 403

        # admins can only register customers in their own organisation
        if request_payload_org.id != admin_data["org_id"] and admin == "admin":
            return False, {"error": "You can only register customers in your own organisation"}, 403

        return True, admin_data, None

    # Helper functions
    def get_organisation(self, org_id):
        organisation = Organisation.query.filter_by(
            id=org_id).first()
        if not organisation:
            return None

        return organisation

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
    def validate_organisation_payload(self, data):
        missing_fields = [
            field for field in self.required_org_fields if not data.get(field)]
        if missing_fields:
            return False, {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        org_type = data["type"].lower()
        if org_type not in self.valid_org_types:
            return False, {"error": f"Invalid organization type: {org_type}"}, 400

        if org_type == "hospital":
            hospital_category = data.get("hospital_category")
            if hospital_category not in self.valid_hospital_categories:
                return False, {
                    "error": "hospital_category must be 'public', 'private', or None"
                }, 400

        return True, None

    def validate_user_payload(self, data):
        # Check for missing fields
        missing_fields = [
            field for field in self.required_user_fields if not data.get(field)
        ]
        if missing_fields:
            return False, {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        # Validate national ID is numeric
        if not str(data.get("national_id")).isdigit():
            return False, {"error": "National ID must be a numeric value"}, 400

        # Validate gender
        gender = data.get("gender", "").lower()
        if gender not in ["male", "female", "other"]:
            return False, {"error": "Gender must be 'male', 'female', or 'other'"}, 400

        # Validate date of birth
        try:
            dob = datetime.strptime(data.get("dob"), "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365
            if age < 18:
                return False, {"error": "User must be at least 18 years old"}, 400
        except ValueError:
            return False, {"error": "Invalid date of birth format. Use 'YYYY-MM-DD'"}, 400

        # Validate mobile number exists and is non-empty
        if not data.get("mobile_number"):
            return False, {"error": "Mobile number is required"}, 400

        # Validate the organisation exists
        organisation = self.get_organisation(data["org_id"])
        if not organisation:
            return False, {"error": f"Organisation with ID {data['org_id']} not found"}, 404

        # Validate if the user exists
        user = User.query.filter_by(
            national_id=data["national_id"]).first()
        if user:
            return False, {"error": "User already exists"}, 409

        return True, None, None

    def validate_insurance_customer_payload(self, data):
        # Check for missing fields
        missing_fields = [
            field for field in self.required_insurance_customer_fields if not data.get(field)
        ]
        if missing_fields:
            return False, {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        # Validate premium_amount is numeric and greater than 0
        try:
            premium_amount = float(data.get("premium_amount", 0))
            if premium_amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return False, {"error": "The premium amount must be a numeric value greater than 0"}, 400

        # Validate the organisation exists
        organisation = self.get_organisation(data.get("org_id"))
        if not organisation:
            return False, {"error": f"Organisation with ID {data.get('org_id')} not found"}, 404

        # All validations passed
        return True, None, None

    # Registration functions
    def register_organisation(self, request):
        token = jwt_service.get_token_from_request(request)
        if not token:
            return {"error": "Unauthorized", "message": "Missing token"}, 401

        # Validate super admin
        can_create_organisation, admin_data = self.can_create_organisation(
            token)
        if not can_create_organisation:
            return admin_data, 401

        # Validate request payload
        data = request.json
        is_payload_valid, payload_error = self.validate_organisation_payload(
            data)
        if not is_payload_valid:
            return payload_error, 400

        # Check if an organization with the same email, name, or KRA PIN already exists
        existing_org = Organisation.query.filter(
            (Organisation.email_address == data["email_address"]) |
            (Organisation.name == data["name"]) |
            (Organisation.kra_pin == data["kra_pin"])
        ).first()

        if existing_org:
            return {"error": "Organization with the same name, email, or KRA PIN already exists"}, 409

        # Create the organization
        unique_code = str(uuid.uuid4())
        new_org = Organisation(
            code=unique_code,
            name=data["name"],
            type=data["type"].lower(),
            kra_pin=data["kra_pin"],
            head_quarter_location=data["head_quarter_location"],
            email_address=data["email_address"],
            mobile_number=data["mobile_number"],
            hospital_category=data.get("hospital_category"),
            status_code="02",
            status_description="Active",
            created_by=admin_data["user_name"],
            approved_by=admin_data["user_name"],
            approved_at=datetime.utcnow(),
        )

        # Save to the database
        try:
            db.session.add(new_org)
            db.session.commit()

            return {
                "message": "Organization created successfully",
                "data": {
                    "id": new_org.id,
                    "code": new_org.code,
                    "name": new_org.name,
                    "type": new_org.type,
                    "email_address": new_org.email_address,
                    "mobile_number": new_org.mobile_number,
                    "hospital_category": new_org.hospital_category,
                }
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback the transaction to maintain consistency
            # Log the error for debugging purposes
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while creating the organization. Please try again later."}, 500

    def register_user(self, request):

        data = request.json

        # Validate the request payload
        is_payload_valid, payload_error, payload_error_code = self.validate_user_payload(
            data)
        if not is_payload_valid:
            return payload_error, payload_error_code

        # Validate if the registration is for an insurance customer
        is_insurance_customer = data.get("type") == "insurance_customer"
        if is_insurance_customer:
            # Validate the insurance customer payload
            is_payload_valid, payload_error, payload_error_code = self.validate_insurance_customer_payload(
                data)
            if not is_payload_valid:
                return payload_error, payload_error_code

        # Validate if the current user can create a user
        can_create, admin_data_or_error, error_code = self.can_create_user(
            request, data)
        if not can_create:
            return admin_data_or_error, error_code

        # Create the user
        # Determine the role based on the organisation type
        organisation = self.get_organisation(data["org_id"])
        if organisation.type == "provider":
            role_name = "super_admin"
        else :
            role_name = "admin"

        role= Role.query.filter_by(role_code=role_name).first()
        if role is None:
        
         return {"error": f"Role {role_name} not found in the database"}, 400
        role_id =role.id
    
        
        
        random_password = generate_strong_password()

        new_user = User(
            user_name=data["user_name"],
            first_name=data["first_name"],
            second_name=data["second_name"] or None,
            last_name=data["last_name"],
            national_id=data["national_id"],
            email=data["email"],
            gender=data["gender"],
            dob=data["dob"],
            mobile_number=data["mobile_number"],
            password_hash=generate_password_hash(random_password),
            role_id=role_id,
            org_id=data["org_id"],
            created_by=admin_data_or_error["user_name"],
            approved_by=admin_data_or_error["user_name"],
            status_code="02",
            status_description="Active",
        )

        try:

            print(f"New user created: {new_user.user_name}")
            print(f"Password: {random_password}")

            email_sent_successfully = send_password_email(
                new_user.email,
                new_user.user_name,
                random_password,
                role_name,
                organisation.name
            )

            db.session.add(new_user)
            db.session.commit()

            return {
                "message": "User created successfully",
                "data": {
                    "id": new_user.id,
                    "user_name": new_user.user_name,
                    "first_name": new_user.first_name,
                    "second_name": new_user.second_name,
                    "last_name": new_user.last_name,
                    "national_id": new_user.national_id,
                    "email": new_user.email,
                    "gender": new_user.gender,
                    "dob": new_user.dob,
                    "mobile_number": new_user.mobile_number,
                    "organisation": organisation.name,
                    "role": role_name,
                    "created_by": admin_data_or_error["user_name"],
                    "status": new_user.status_description,
                    "email_sent_successfully": email_sent_successfully
                }
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback the transaction to maintain consistency
            # Log the error for debugging purposes
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while creating the user. Please try again later."}, 500

    def register_insurance_customer(self, request):

        data = request.json

        # Validate the request payload
        is_user_payload_valid, user_payload_error, user_payload_error_code = self.validate_user_payload(
            data)
        is_insurance_customer_payload_valid, insurance_customer_payload_error, insurance_customer_payload_error_code = self.validate_insurance_customer_payload(
            data)

        if not is_user_payload_valid:
            return user_payload_error, user_payload_error_code

        if not is_insurance_customer_payload_valid:
            return insurance_customer_payload_error, insurance_customer_payload_error_code

        # Validate if the current user can create a user
        can_create, admin_data_or_error, error_code = self.can_create_insurance_customer(
            request, data)
        if not can_create:
            return admin_data_or_error, error_code

        # Create the user
        # Determine the role based on the organisation type
        organisation = self.get_organisation(data["org_id"])
        role_name = "user"

        role = Role.query.filter_by(role_code=role_name).first()
        if role is None:
        # Handle the case where the role does not exist
         raise ValueError(f"Role with role_code '{role_name}' not found.")

        role_id = role.id

        random_password = generate_strong_password()

        insurance_customer = User(
            user_name=data["user_name"],
            first_name=data["first_name"],
            second_name=data["second_name"] or None,
            last_name=data["last_name"],
            national_id=data["national_id"],
            email=data["email"],
            gender=data["gender"],
            dob=data["dob"],
            mobile_number=data["mobile_number"],
            password_hash=generate_password_hash(random_password),
            role_id=role_id,
            org_id=data["org_id"],
            created_by=admin_data_or_error["user_name"],
            approved_by=admin_data_or_error["user_name"],
            status_code="01",
            status_description="Active",
        )

        try:
            db.session.add(insurance_customer)
            db.session.commit()

            print(f"New user created: {insurance_customer.user_name}")
            print(f"Password: {random_password}")

            # Create the insurance customer Policy
            duration = timedelta(days=365)  # 1 year
            policy_start_date = datetime.utcnow()
            policy_end_date = policy_start_date + duration
            policy_number = generate_policy_number()

            new_policy = Policy(
                policy_number=policy_number,
                policy_start_date=policy_start_date.date(),
                policy_end_date=policy_end_date.date(),
                premium_amount=data["premium_amount"],
                remaining_limit=data["premium_amount"],
                user_id=insurance_customer.id,
            )

            # Create the insurance customer policy
            db.session.add(new_policy)
            db.session.commit()

            # Send the password to the user's email
            email_sent_successfully = send_password_email(
                insurance_customer.email,
                insurance_customer.user_name,
                random_password,
                role_name,
                organisation.name,

            )

            return {
                "message": "User created successfully",
                "data": {
                    "id": insurance_customer.id,
                    "user_name": insurance_customer.user_name,
                    "first_name": insurance_customer.first_name,
                    "second_name": insurance_customer.second_name,
                    "last_name": insurance_customer.last_name,
                    "national_id": insurance_customer.national_id,
                    "email": insurance_customer.email,
                    "gender": insurance_customer.gender,
                    "dob": insurance_customer.dob,
                    "mobile_number": insurance_customer.mobile_number,
                    "organisation": organisation.name,
                    "role": role_name,
                    "created_by": admin_data_or_error["user_name"],
                    "status": insurance_customer.status_description,
                    "email_sent_successfully": email_sent_successfully,

                    "policy_number": new_policy.policy_number,
                    "policy_start_date": new_policy.policy_start_date,
                    "policy_end_date": new_policy.policy_end_date,
                    "premium_amount": new_policy.premium_amount,
                    "remaining_limit": new_policy.remaining_limit,
                }
            }, 201

        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback the transaction to maintain consistency
            # Log the error for debugging purposes
            print(f"Database error: {str(e)}", flush=True)
            return {"error": "An error occurred while creating the insurance customer. Please try again later."}, 500


registration_service = RegistrationService()
