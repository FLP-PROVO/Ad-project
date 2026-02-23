from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.gift_code import GiftCode
from app.models.user import User, UserRole


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="gift-admin@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def _create_viewer(db_session: Session, email: str = "gift-viewer@example.com") -> User:
    viewer = User(
        email=email,
        password_hash=hash_password("secret-password"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer


def test_admin_can_upload_and_list_gift_codes(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    upload_response = client.post(
        "/api/v1/admin/gift-codes",
        json={"provider": "amazon", "codes": ["AMZ-001", "AMZ-002"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    assert len(upload_body) == 2
    assert all(row["provider"] == "amazon" for row in upload_body)

    stored_codes = db_session.query(GiftCode).all()
    assert len(stored_codes) == 2

    list_response = client.get(
        "/api/v1/admin/gift-codes?redeemed=false",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 2
    assert all(item["redeemed"] is False for item in listed)


def test_upload_rejects_duplicate_codes(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    first_response = client.post(
        "/api/v1/admin/gift-codes",
        json={"provider": "external_provider", "codes": ["DUP-001"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/api/v1/admin/gift-codes",
        json={"provider": "external_provider", "codes": ["DUP-001"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert duplicate_response.status_code == 409


def test_admin_can_assign_code_to_user(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)
    viewer = _create_viewer(db_session)

    upload_response = client.post(
        "/api/v1/admin/gift-codes",
        json={"provider": "amazon", "codes": ["ASSIGN-001"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload_response.status_code == 201

    assign_response = client.post(
        "/api/v1/admin/redeem-code",
        json={"code": "ASSIGN-001", "user_id": str(viewer.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign_response.status_code == 200
    body = assign_response.json()
    assert body["code"] == "ASSIGN-001"
    assert body["assigned_to_user_id"] == str(viewer.id)
    assert body["redeemed"] is False
