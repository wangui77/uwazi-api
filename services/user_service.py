from models.user import User
from werkzeug.security import check_password_hash, generate_password_hash

from services.db_service import db


class UserService:
    @staticmethod
    def verify_user(email, password):
        try:
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                return user
            return None
        except Exception as e:
            raise Exception(f"Failed to verify user: {str(e)}")

    @staticmethod
    def create_user(firstname, lastname, email, password, org_id):
        try:
            hashed_password = generate_password_hash(password)
            new_user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                org_id=org_id,
                password_hash=hashed_password,
            )
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create user: {str(e)}")


user_service = UserService()
