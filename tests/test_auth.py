from fastapi.testclient import TestClient
from uuid import uuid4

from server.main import app


def test_register_duplicate_returns_generic_error() -> None:
    email = f"user_{uuid4().hex[:12]}@a.com"
    payload = {"email": email, "password": "strongpass123"}
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        r2 = client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 400
        assert r2.json()["detail"] == "Unable to complete registration"


def test_register_and_login_success() -> None:
    email = f"user_{uuid4().hex[:12]}@a.com"
    register_payload = {
        "email": email,
        "password": "strongpass123",
    }
    with TestClient(app) as client:
        register_response = client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201
        assert register_response.json()["user"]["email"] == register_payload["email"]

        login_response = client.post("/api/v1/auth/login", json=register_payload)
        assert login_response.status_code == 200
        body = login_response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"


def test_register_reject_invalid_domain() -> None:
    payload = {
        "email": f"user_{uuid4().hex[:12]}@c.com",
        "password": "strongpass123",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400
        assert "Domain is not allowed" in response.json()["detail"]


def test_register_reject_password_without_letter() -> None:
    payload = {
        "email": f"user_{uuid4().hex[:12]}@a.com",
        "password": "12345678",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400
        assert "at least one letter" in response.json()["detail"]


def test_register_reject_password_without_number() -> None:
    payload = {
        "email": f"user_{uuid4().hex[:12]}@a.com",
        "password": "abcdefgh",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400
        assert "at least one number" in response.json()["detail"]


def test_register_reject_password_too_short() -> None:
    payload = {
        "email": f"user_{uuid4().hex[:12]}@a.com",
        "password": "a1b2c3",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


def test_login_lock_after_five_failed_attempts() -> None:
    email = f"user_{uuid4().hex[:12]}@a.com"
    password = "strongpass123"
    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert register_response.status_code == 201

        for _ in range(4):
            bad_response = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "wrongpass999"},
            )
            assert bad_response.status_code == 401

        lock_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrongpass999"},
        )
        assert lock_response.status_code == 423
        assert "locked" in lock_response.json()["detail"].lower()

        still_locked_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert still_locked_response.status_code == 423
