import secrets
import string
import uuid


def generate_strong_password(length=12):
    """
    Generate a strong random password.
    """
    characters = string.ascii_letters + string.digits + string.ascii_uppercase
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def generate_policy_number():
    """Generate a unique policy number using UUID."""
    policy_number = f"POL-{str(uuid.uuid4())[:8]}"  # Use the first 8 characters of the UUID for brevity
    return policy_number.upper()
