import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "D2A Health API")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    frontend_origins: str = os.getenv("FRONTEND_ORIGINS", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./d2a_health.db")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    gemini_timeout_seconds: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "8"))
    demo_login_email: str = os.getenv("DEMO_LOGIN_EMAIL", "demo@d2a.health")
    demo_login_password: str = os.getenv("DEMO_LOGIN_PASSWORD", "demo-password")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_timeout_seconds: float = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    # Brevo uses HTTPS, so it works on Render Free without SMTP ports.
    email_provider: str = os.getenv("EMAIL_PROVIDER", "brevo").lower()
    brevo_api_key: str = os.getenv("BREVO_API_KEY", "")
    email_from: str = os.getenv("EMAIL_FROM", "")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "D2A Health")
    email_logo_url: str = os.getenv("EMAIL_LOGO_URL", "")
    email_timeout_seconds: float = float(os.getenv("EMAIL_TIMEOUT_SECONDS", "10"))


settings = Settings()
