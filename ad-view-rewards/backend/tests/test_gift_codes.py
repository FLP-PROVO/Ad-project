from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.gift_code import GiftCode
from app.models.user import User, UserRole


def _create_admin_token(db_session: Session) -> str:
    admin = User(email="codes-admin@example.com", password_hash=hash_password("secret-password"), role=UserRole.admin)
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_csv_upload_requires_provider_query_param(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    response = client.post(
        "/api/v1/admin/gift-codes",
        data="code\nCSV-001",
        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "text/csv"},
    )

    assert response.status_code == 422


def test_assigning_missing_code_returns_not_found(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    assign_response = client.post(
        "/api/v1/admin/redeem-code",
        json={"code": "UNKNOWN-CODE", "user_id": "00000000-0000-0000-0000-000000000001"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign_response.status_code == 404

    assert db_session.query(GiftCode).count() == 0
