"""
The purpose of this file is to create a Celery task(CRON job) that can be used to clean up expired tokens from the database.

"""

from celery import Celery

from app import create_app
from app.services.jwt_service import jwt_service

# Create the Flask app and Celery instance
app = create_app()
celery = Celery(app.name, broker="redis://localhost:6379/0")


@celery.task
def cleanup_expired_tokens_task():
    """
    Celery task to clean up expired tokens from the database.
    """
    with app.app_context():
        jwt_service.cleanup_expired_tokens()
        print("Expired tokens cleaned up successfully.")
