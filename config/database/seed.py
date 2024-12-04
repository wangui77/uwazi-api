import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from models.organisation import Organisation
from models.role import Role
from models.user import User
from services.db_service import db

load_dotenv()


def seed():
    # Load env vars
    default_org_name = os.getenv("DEFAULT_ORG_NAME", "Uwazi Systems")
    default_admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@uwazi.com")
    default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "password")
    default_admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")

    # Seed roles
    roles = [
        {
            "role_code": "admin",
            "role_description": "Administrator with general privileges",
            "created_by": "system",
            "created_at": datetime.utcnow(),
        },
        {
            "role_code": "super_admin",
            "role_description": "Super Administrator with all privileges",
            "created_by": "system",
            "created_at": datetime.utcnow(),
        },
        {
            "role_code": "user",
            "role_description": "User with limited privileges",
            "created_by": "system",
            "created_at": datetime.utcnow(),
        },
    ]

    for role_data in roles:
        if not Role.query.filter_by(role_code=role_data["role_code"]).first():
            db.session.add(Role(**role_data))

    # Seed default organisation
    unique_code = str(uuid.uuid4())
    default_org = {
        "type": "provider",
        "code": unique_code,
        "name": default_org_name,
        "created_by": default_admin_username,
        "approved_by": default_admin_username,
        "approved_at": datetime.utcnow(),
    }

    organisation = Organisation.query.filter_by(
        type=default_org["type"]
    ).first()

    if not organisation:
        organisation = Organisation(**default_org)
        db.session.add(organisation)
        db.session.flush()

    # Seed super admin user
    role_id = Role.query.filter_by(role_code="super_admin").first().id
    super_admin = {
        "user_name": default_admin_username,
        "first_name": default_admin_username,
        "second_name": default_admin_username,
        "last_name": default_admin_username,
        "email": default_admin_email,
        "password_hash": generate_password_hash(default_admin_password),
        "role_id": role_id,
        "org_id": organisation.id,
        "created_by": default_admin_username,
        "approved_by": default_admin_username,
        "status_code": "02",
        "status_description": "Active",
        "created_at": datetime.utcnow(),
    }
    if not User.query.filter_by(user_name=super_admin["user_name"]).first():
        db.session.add(User(**super_admin))

    db.session.commit()
