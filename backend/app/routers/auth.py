import hashlib
import hmac
import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.db import SessionLocal, init_db
from app.db_models import UserRow
from app.models import LoginRequest, LoginResponse, SignupRequest, UserProfile, UserRole

router = APIRouter()


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> LoginResponse:
    email = payload.email.strip().lower()
    user = UserProfile(
        email=email,
        name=payload.name.strip(),
        role=UserRole.health_data_analyst,
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
        )
    )


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
