import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_password_email(to_email, username, password, role, organisation):
    """
    Send the generated password to the user's email.
    """
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")
    smtp_server = "smtp.gmail.com"  # Use the SMTP server for your email provider
    smtp_port = 587

    # Email content
    subject = "Account Password"
    html_body = f"""
    <html>
        <body>
            <p>
                Hello <strong>{username}</strong>,</p>
            <p>
                Your account has been created successfully.Please find the details below:
                <br>
                <br>
                <strong>Username:</strong> {username}<br>
                <strong>Password:</strong><span style="font-size: 18px; color: blue;"> {password}</span><br>
                <strong>Organisation:</strong> {organisation}<br>
                <strong>Role:</strong> {role}<br>

            </p>
            <br>
            <p>Best regards,<br><strong>Uwazi Team</strong></p>
        </body>
    </html>
    """

    # Create the email
    msg = MIMEMultipart("alternative")  # Allows multiple content types
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach the HTML content
    msg.attach(MIMEText(html_body, "html"))

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("Email sent successfully.", flush=True)
        return True
    except Exception as e:
        # Log the error and sensitive data (for debugging purposes, ensure this is safe in your environment)
        print(f"Failed to send email: {e}", flush=True)
        print(
            f"Debug Info: username={username}, to_email={to_email}, password={password}, sender_email={sender_email}, sender_password={sender_password}", flush=True)
        return False
