import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "D2A Health API")
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./d2a_health.db")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    gemini_timeout_seconds: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "8"))
    demo_login_email: str = os.getenv("DEMO_LOGIN_EMAIL", "demo@d2a.health")
    demo_login_password: str = os.getenv("DEMO_LOGIN_PASSWORD", "demo-password")


settings = Settings()
