import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.db import SessionLocal, init_db
from app.db_models import UserRow, VerificationCodeRow
from app.models import EmailVerificationRequest, LoginRequest, LoginResponse, PasswordResetConfirm, PasswordResetRequest, SignupRequest, SignupResponse, UserProfile, UserRole
from app.services.email_service import EmailDeliveryError, email_is_configured, send_otp_email

router = APIRouter()
CODE_EXPIRY = timedelta(minutes=10)


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> SignupResponse:
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
                    email_verified=False,
                )
            )
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="User database is currently unavailable.")

    code = _create_code(email, "signup")
    development_code = _deliver_code(email, code, "signup")
    return SignupResponse(
        message="Account created. Check your email for the verification code.",
        development_code=development_code,
    )


@router.post("/verify-email")
def verify_email(payload: EmailVerificationRequest) -> dict[str, str]:
    email = payload.email.strip().lower()
    if not _valid_code(email, "signup", payload.code):
        raise HTTPException(status_code=400, detail="The verification code is invalid or expired.")
    try:
        init_db()
        with SessionLocal.begin() as session:
            user = session.get(UserRow, email)
            if not user:
                raise HTTPException(status_code=404, detail="Account not found.")
            user.email_verified = True
            _delete_codes(session, email, "signup")
    except HTTPException:
        raise
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="User database is currently unavailable.")
    return {"message": "Email verified successfully. You can now sign in."}


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

    if not stored_user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before signing in.")

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
        code = _create_code(email, "reset")
        development_code = _deliver_code(email, code, "reset")
        response = {"message": "If an account exists for that email, a reset code has been sent."}
        if development_code:
            response["development_code"] = development_code
        return response

    return {"message": "If an account exists for that email, a reset code has been sent."}


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm) -> dict[str, str]:
    email = payload.email.strip().lower()
    if not _valid_code(email, "reset", payload.code):
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

    with SessionLocal.begin() as session:
        _delete_codes(session, email, "reset")
    return {"message": "Password reset successfully. You can now sign in."}


def _create_code(email: str, purpose: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    try:
        init_db()
        with SessionLocal.begin() as session:
            _delete_codes(session, email, purpose)
            session.add(
                VerificationCodeRow(
                    email=email,
                    purpose=purpose,
                    code_hash=hashlib.sha256(code.encode()).hexdigest(),
                    expires_at=datetime.now(timezone.utc) + CODE_EXPIRY,
                )
            )
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Could not store the verification code.")
    return code


def _deliver_code(email: str, code: str, purpose: str) -> str | None:
    try:
        send_otp_email(email, code, purpose)
    except EmailDeliveryError:
        if settings.app_env == "development" and not email_is_configured():
            return code
        raise HTTPException(status_code=503, detail="Email delivery is not configured or unavailable.")
    return None


def _valid_code(email: str, purpose: str, code: str) -> bool:
    try:
        init_db()
        with SessionLocal() as session:
            entry = (
                session.query(VerificationCodeRow)
                .filter_by(email=email, purpose=purpose)
                .order_by(VerificationCodeRow.id.desc())
                .first()
            )
            if not entry:
                return False
            expires_at = entry.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return bool(
                expires_at >= datetime.now(timezone.utc)
                and hmac.compare_digest(entry.code_hash, hashlib.sha256(code.encode()).hexdigest())
            )
    except SQLAlchemyError:
        return False


def _delete_codes(session, email: str, purpose: str) -> None:
    session.query(VerificationCodeRow).filter_by(email=email, purpose=purpose).delete()


def _is_demo_user(email: str, password: str) -> bool:
    configured_match = hmac.compare_digest(email, settings.demo_login_email.lower()) and hmac.compare_digest(
        password, settings.demo_login_password
    )
    legacy_match = hmac.compare_digest(email, "demo@d2a.health") and hmac.compare_digest(
        password, "demo-password"
    )
    return configured_match or legacy_match


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
