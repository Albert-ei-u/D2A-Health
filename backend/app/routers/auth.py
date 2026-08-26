import hmac

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.models import LoginRequest, LoginResponse, UserProfile, UserRole


router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest) -> LoginResponse:
    valid_email = hmac.compare_digest(
        payload.email.strip().lower(), settings.demo_login_email.lower()
    )
    valid_password = hmac.compare_digest(payload.password, settings.demo_login_password)
    if not (valid_email and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = UserProfile(
        email=settings.demo_login_email,
        name="D2A Demo User",
        role=UserRole.health_data_analyst,
    )
    return LoginResponse(
        access_token="demo-token",
        user=user,
        name=user.name,
        role=user.role,
        email=user.email,
    )
