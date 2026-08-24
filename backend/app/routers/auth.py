from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    return {
        "access_token": "demo-token",
        "token_type": "bearer",
        "name": "D2A Demo User",
        "role": "Health Data Analyst",
        "email": payload.email,
    }
