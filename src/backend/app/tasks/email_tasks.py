import os
import logging
import smtplib
from email.message import EmailMessage

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.send_verification_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_verification_email(self, to_email: str, subject: str, body: str) -> bool:
    """Send verification email using smtplib. Retries on exceptions.

    Returns True on success, False when SMTP not configured.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not (smtp_host and smtp_port and smtp_user and smtp_pass):
        logger.warning("SMTP not configured, skipping email send")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg.set_content(body)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        logger.info("verification email queued/sent to %s", to_email)
        return True
    except Exception as e:
        logger.exception("failed to send verification email to %s: %s", to_email, e)
        # re-raise to allow Celery autoretry
        raise
