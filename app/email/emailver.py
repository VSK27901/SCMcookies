from email.message import EmailMessage
import ssl
import smtplib
from email.utils import make_msgid
from dotenv import load_dotenv
import os

load_dotenv()


EMAIL_SENDER = os.getenv("EMAIL_SENDER")  
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST") 
EMAIL_PORT = os.getenv("EMAIL_PORT")

def send_verification_email(username, email, verification_token):
    subject = "Email Verification"
    sender_email = EMAIL_SENDER
    receiver_email = email

    # Generate a unique message ID for the email
    message_id = make_msgid(domain="yourdomain.com")

    em = EmailMessage()
    em["Message-ID"] = message_id
    em["From"] = sender_email
    em["To"] = receiver_email
    em["Subject"] = subject

    # Email body with a verification link
    body = f"Hello {username},\n\nPlease click the following link to verify your email address:\n"
    verification_link = f"http://127.0.0.1:8000/verification?token={verification_token}"  
    body += verification_link
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(em)
        print("Verification email sent successfully!")
    except Exception as e:
        print("Error sending verification email:", str(e))
