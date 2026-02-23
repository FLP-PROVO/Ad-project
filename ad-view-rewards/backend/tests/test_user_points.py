import uuid

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.points_ledger import PointsLedger
from app.models.user import User, UserRole


def _create_user(db_session: Session, email: str) -> tuple[User, str]:
    user = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, create_access_token(subject=user.email)


def _add_ledger_entry(db_session: Session, user_id: uuid.UUID, change: int, reason: str) -> None:
    db_session.add(
        PointsLedger(
            user_id=user_id,
            change=change,
            reason=reason,
            reference_id=uuid.uuid4(),
        )
    )
    db_session.commit()


def test_balance_matches_sum_of_ledger_for_current_user(client, db_session: Session) -> None:
    user, token = _create_user(db_session, "ledger-user@example.com")
    other_user, _ = _create_user(db_session, "other-ledger-user@example.com")

    _add_ledger_entry(db_session, user.id, 10, "ad_reward")
    _add_ledger_entry(db_session, user.id, -3, "adjustment")
    _add_ledger_entry(db_session, other_user.id, 500, "ad_reward")

    response = client.get("/api/v1/users/me/balance", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["balance"] == 7


def test_ledger_returns_paginated_and_user_filtered_entries(client, db_session: Session) -> None:
    user, token = _create_user(db_session, "ledger-page@example.com")
    other_user, _ = _create_user(db_session, "ledger-page-other@example.com")

    for idx in range(5):
        _add_ledger_entry(db_session, user.id, idx + 1, f"reason-{idx}")
    _add_ledger_entry(db_session, other_user.id, 999, "other")

    response = client.get(
        "/api/v1/users/me/ledger?page=2&limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 2
    assert body["limit"] == 2
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert all(item["user_id"] == str(user.id) for item in body["items"])


def test_points_endpoints_require_authentication(client) -> None:
    balance_response = client.get("/api/v1/users/me/balance")
    ledger_response = client.get("/api/v1/users/me/ledger")

    assert balance_response.status_code == 401
    assert ledger_response.status_code == 401
