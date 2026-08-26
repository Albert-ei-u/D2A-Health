from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_login_returns_user_and_role() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@d2a.health", "password": "demo-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"].startswith("mvp-")
    assert payload["user"]["role"] == "Health Data Analyst"
    assert payload["role"] == "Health Data Analyst"


def test_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@d2a.health", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_validation_errors_use_api_error_shape() -> None:
    response = client.post("/api/auth/login", json={"email": ""})

    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed."
    assert response.json()["errors"]
