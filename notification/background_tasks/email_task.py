
from utils.config import *
from email.message import EmailMessage
from loggers.logger import logger
import aiosmtplib

async def send_email_task(to_email: str, subject: str, body: str):
    """Function to send email asynchronously."""
    email = EmailMessage()
    email["From"] = SMTP_USER
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(body)

    # Send the email
    try:
        await aiosmtplib.send(
            email,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=False,  # Use STARTTLS instead
            start_tls=True,
        )
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.info(f"Failed to send email to {to_email}: {str(e)}")