import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass


def email_is_configured() -> bool:
    return all(
        (
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_from_email,
        )
    )


def send_otp_email(recipient: str, code: str, purpose: str) -> None:
    if not email_is_configured():
        raise EmailDeliveryError("Email delivery is not configured.")

    subject = "Verify your D2A Health account" if purpose == "signup" else "Reset your D2A Health password"
    action = "verify your email address" if purpose == "signup" else "reset your password"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        f"Your D2A Health code is {code}. Use it to {action}. "
        "This code expires in 10 minutes. If you did not request this, ignore this email."
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("The email provider could not deliver the code.") from error
