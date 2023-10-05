from email.message import EmailMessage
import ssl
import smtplib
from email.utils import make_msgid
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # email and password
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST")  # SMTP server
EMAIL_PORT = os.getenv("EMAIL_PORT")  # port number of SMTP server


def send_passreset_email(email, reset_password_token):
    subject = "Password Reset Link"
    sender_email = EMAIL_SENDER
    receiver_email = email

    # Generate a unique message ID for the email
    message_id = make_msgid(domain="yourdomain.com")

    em = EmailMessage()
    em["Message-ID"] = message_id
    em["From"] = sender_email
    em["To"] = receiver_email
    em["Subject"] = subject

    # Email body with a reset password link
    body = f"Please click the following link to reset your password:\n"
    resetpass_link = f"http://127.0.0.1:8000/resetpassword?token={reset_password_token}"  # Include the token in the reset link
    body += resetpass_link
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(em)
        print("Password Reset link sent successfully!")
    except Exception as e:
        print("Error sending password reset email:", str(e))