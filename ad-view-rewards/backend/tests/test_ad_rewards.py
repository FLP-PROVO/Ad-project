from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole


def _create_viewer_with_token(db_session: Session, email: str = "viewer-reward@example.com") -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def _create_ad(
    db_session: Session,
    reward_point: int = 10,
    budget: int = 100,
    file_path: str | None = None,
    duration_seconds: int | None = None,
) -> Ad:
    ad = Ad(
        advertiser_id=None,
        title="Rewarded Ad",
        video_url="https://example.com/rewarded.mp4",
        file_path=file_path,
        duration_seconds=duration_seconds,
        reward_point=reward_point,
        budget=budget,
        remaining_budget=budget,
        is_active=True,
        status="ready",
    )
    db_session.add(ad)
    db_session.commit()
    db_session.refresh(ad)
    return ad


def test_available_ads_returns_only_active_with_budget(client, db_session: Session) -> None:
    _, token = _create_viewer_with_token(db_session, email="viewer-available@example.com")

    eligible_ad = _create_ad(db_session, reward_point=10, budget=50, file_path="/media/ads/eligible.mp4", duration_seconds=30)
    ineligible_ad = _create_ad(db_session, reward_point=100, budget=100, file_path="/media/ads/ineligible.mp4", duration_seconds=30)
    ineligible_ad.remaining_budget = 10
    db_session.commit()

    inactive_ad = _create_ad(db_session, reward_point=10, budget=50, file_path="/media/ads/inactive.mp4", duration_seconds=30)
    inactive_ad.is_active = False
    db_session.commit()

    response = client.get("/api/v1/ads/available", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    body = response.json()
    ad_ids = {item["id"] for item in body}
    assert str(eligible_ad.id) in ad_ids
    assert str(ineligible_ad.id) not in ad_ids
    assert str(inactive_ad.id) not in ad_ids
