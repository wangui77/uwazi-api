import os
from datetime import datetime

from models.organisation import Organisation
from models.role import Role
from models.user import User
from services.db_service import db
from werkzeug.security import generate_password_hash


def seed():
    """Seed the database with default data."""

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
    ]

    for role_data in roles:
        if not Role.query.filter_by(role_code=role_data["role_code"]).first():
            db.session.add(Role(**role_data))

    # Seed default organisation
    default_org = {
        "code": "PROVIDER",
        "name": "Uwazi",
        "type": "provider",
        "created_by": "system",
        "approved_by": "system",
        "approved_at": datetime.utcnow(),
    }

    organisation = Organisation.query.filter_by(
        code=default_org["code"]
    ).first()

    if not organisation:
        organisation = Organisation(**default_org)
        db.session.add(organisation)
        db.session.flush()

    # Seed super admin user
    super_admin = {
        "user_name": "uwazi_admin",
        "first_name": "Uwazi",
        "last_name": "Admin",
        "email": "uwazi_admin@email.com",
        "password_hash": generate_password_hash("password"),
        "role_id": Role.query.filter_by(role_code="super_admin").first().id,
        "org_id": organisation.id,
        "created_by": "system",
        "status_code": "active",
        "created_at": datetime.utcnow(),
    }
    if not User.query.filter_by(user_name=super_admin["user_name"]).first():
        db.session.add(User(**super_admin))

    db.session.commit()
