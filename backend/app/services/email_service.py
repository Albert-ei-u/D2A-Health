import json
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(RuntimeError):
    pass


def email_is_configured() -> bool:
    if settings.email_provider == "brevo":
        return bool(settings.brevo_api_key and settings.email_from)
    return all((settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from_email))


def send_otp_email(recipient: str, code: str, purpose: str) -> None:
    if not email_is_configured():
        raise EmailDeliveryError("Email delivery is not configured.")

    subject = "Verify your D2A Health account" if purpose == "signup" else "Reset your D2A Health password"
    action = "verify your email address" if purpose == "signup" else "reset your D2A Health password"
    text = f"Your D2A Health code is {code}. Use it to {action}. This code expires in 10 minutes. If you did not request this, ignore this email."
    html = _email_html(subject, text, code)

    if settings.email_provider == "brevo":
        _send_with_brevo(recipient, subject, text, html)
    else:
        _send_with_smtp(recipient, subject, text, html)


def _send_with_brevo(recipient: str, subject: str, text: str, html: str) -> None:
    body = json.dumps({
        "sender": {"name": settings.email_from_name, "email": settings.email_from},
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": text,
        "htmlContent": html,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=body,
        headers={"accept": "application/json", "api-key": settings.brevo_api_key, "content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.email_timeout_seconds) as response:
            if response.status < 200 or response.status >= 300:
                raise EmailDeliveryError("Brevo rejected the email request.")
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as error:
        raise EmailDeliveryError("Brevo could not deliver the code.") from error


def _send_with_smtp(recipient: str, subject: str, text: str, html: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("The email provider could not deliver the code.") from error


def _email_html(subject: str, text: str, code: str) -> str:
    logo = ""
    if settings.email_logo_url:
        logo = f'<img src="{settings.email_logo_url}" alt="D2A Health" width="72" height="72" style="display:block;margin:0 auto 18px;" />'
    return f'''<!doctype html>
<html><body style="margin:0;background:#f5fafb;font-family:Arial,sans-serif;color:#082d49;">
  <div style="max-width:520px;margin:32px auto;padding:32px;background:#ffffff;border:1px solid #dce9eb;border-radius:12px;">
    {logo}<h1 style="margin:0 0 12px;text-align:center;font-size:24px;">{subject}</h1>
    <p style="font-size:16px;line-height:1.5;">{text}</p>
    <div style="margin:24px 0;padding:18px;text-align:center;background:#e8f8f7;border-radius:8px;font-size:32px;letter-spacing:8px;font-weight:700;color:#087f82;">{code}</div>
    <p style="font-size:13px;color:#527086;">D2A Health Intelligence</p>
  </div>
</body></html>'''
