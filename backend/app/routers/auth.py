import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.db import SessionLocal, init_db
from app.db_models import UserRow
from app.models import LoginRequest, LoginResponse, PasswordResetConfirm, PasswordResetRequest, SignupRequest, UserProfile, UserRole

router = APIRouter()
_reset_codes: dict[str, tuple[str, datetime]] = {}


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> LoginResponse:
    email = payload.email.strip().lower()
    user = UserProfile(
        email=email,
        name=payload.name.strip(),
        role=UserRole.health_data_analyst,
        health_center=payload.health_center.strip(),
        dataset_ready=False,
    )
    if not user.name:
        raise HTTPException(status_code=422, detail="Name cannot be blank.")

    try:
        init_db()
        with SessionLocal.begin() as session:
            if session.get(UserRow, email):
                raise HTTPException(status_code=409, detail="An account with this email already exists.")
            session.add(
                UserRow(
                    email=user.email,
                    name=user.name,
                    password_hash=_hash_password(payload.password),
                    role=user.role.value,
                    health_center=user.health_center,
                    dataset_ready=user.dataset_ready,
                )
            )
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="User database is currently unavailable.")

    return _login_response(user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    email = payload.email.strip().lower()
    if _is_demo_user(email, payload.password):
        return _login_response(
            UserProfile(
                email=settings.demo_login_email,
                name="D2A Demo User",
                role=UserRole.health_data_analyst,
                health_center="Demo Health Center",
                dataset_ready=False,
            )
        )

    try:
        init_db()
        with SessionLocal() as session:
            stored_user = session.get(UserRow, email)
    except SQLAlchemyError:
        stored_user = None

    if not stored_user or not _verify_password(payload.password, stored_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return _login_response(
        UserProfile(
            email=stored_user.email,
            name=stored_user.name,
            role=UserRole(stored_user.role),
            health_center=stored_user.health_center,
            dataset_ready=stored_user.dataset_ready,
        )
    )


@router.post("/forgot-password")
def forgot_password(payload: PasswordResetRequest) -> dict[str, str]:
    email = payload.email.strip().lower()
    try:
        init_db()
        with SessionLocal() as session:
            user_exists = session.get(UserRow, email) is not None
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="User database is currently unavailable.")

    if user_exists:
        code = f"{secrets.randbelow(1_000_000):06d}"
        _reset_codes[email] = (code, datetime.now(timezone.utc) + timedelta(minutes=10))
        if settings.app_env == "development":
            return {"message": "Reset code generated for development testing.", "development_code": code}

    return {"message": "If an account exists for that email, a reset code has been sent."}


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm) -> dict[str, str]:
    email = payload.email.strip().lower()
    reset_entry = _reset_codes.get(email)
    if not reset_entry or reset_entry[0] != payload.code or reset_entry[1] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="The reset code is invalid or expired.")

    try:
        init_db()
        with SessionLocal.begin() as session:
            user = session.get(UserRow, email)
            if not user:
                raise HTTPException(status_code=400, detail="The reset code is invalid or expired.")
            user.password_hash = _hash_password(payload.new_password)
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="User database is currently unavailable.")

    _reset_codes.pop(email, None)
    return {"message": "Password reset successfully. You can now sign in."}


def _is_demo_user(email: str, password: str) -> bool:
    return hmac.compare_digest(email, settings.demo_login_email.lower()) and hmac.compare_digest(
        password, settings.demo_login_password
    )


def _login_response(user: UserProfile) -> LoginResponse:
    return LoginResponse(
        access_token=f"mvp-{secrets.token_urlsafe(18)}",
        user=user,
        name=user.name,
        role=user.role,
        email=user.email,
        health_center=user.health_center,
        requires_data_upload=not user.dataset_ready,
    )


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, digest_hex = encoded.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return hmac.compare_digest(actual, expected)
