import secrets
import string


def generate_strong_password(length=12):
    """
    Generate a strong random password.
    """
    characters = string.ascii_letters + string.digits + string.ascii_uppercase
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password
