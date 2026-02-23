import uuid

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def _create_viewer_token(db_session: Session) -> str:
    viewer = User(
        email="viewer@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    db_session.commit()
    return create_access_token(subject=viewer.email)


def test_admin_can_create_ad_and_remaining_budget_is_initialized(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    payload = {
        "advertiser_id": None,
        "title": "Test Video Ad",
        "video_url": "https://example.com/video.mp4",
        "reward_point": 10,
        "budget": 100,
        "is_active": True,
    }
    response = client.post(
        "/api/v1/admin/ads",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["remaining_budget"] == payload["budget"]
    assert body["reward_point"] == payload["reward_point"]

    stored_ad = db_session.query(Ad).filter(Ad.id == uuid.UUID(body["id"])).first()
    assert stored_ad is not None
    assert stored_ad.remaining_budget == payload["budget"]


def test_admin_ads_requires_admin_role(client, db_session: Session) -> None:
    viewer_token = _create_viewer_token(db_session)

    response = client.get(
        "/api/v1/admin/ads",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_create_ad_validation_rejects_non_positive_reward_point(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    response = client.post(
        "/api/v1/admin/ads",
        json={
            "title": "Invalid Reward",
            "video_url": "https://example.com/invalid.mp4",
            "reward_point": 0,
            "budget": 10,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


def test_create_ad_validation_rejects_budget_smaller_than_reward(client, db_session: Session) -> None:
    admin_token = _create_admin_token(db_session)

    response = client.post(
        "/api/v1/admin/ads",
        json={
            "title": "Invalid Budget",
            "video_url": "https://example.com/invalid-budget.mp4",
            "reward_point": 50,
            "budget": 30,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422
