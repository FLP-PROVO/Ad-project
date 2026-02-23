from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def test_register_login_and_me_flow(client) -> None:
    register_payload = {
        "email": "viewer@example.com",
        "password": "strong-password",
        "phone_number": "+81123456789",
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert "access_token" in register_body
    assert register_body["token_type"] == "bearer"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    login_token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {login_token}"})
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["email"] == register_payload["email"]
    assert me_body["role"] == "viewer"
    assert me_body["phone_number"] == register_payload["phone_number"]


def test_password_is_hashed_not_plaintext(client, db_session: Session) -> None:
    raw_password = "plaintext-password"
    email = "hash-check@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": raw_password, "phone_number": None},
    )
    assert response.status_code == 201

    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.password_hash != raw_password
    assert verify_password(raw_password, user.password_hash)


def test_protected_endpoint_requires_token(client) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
