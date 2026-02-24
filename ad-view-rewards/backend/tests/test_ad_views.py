from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User, UserRole


def _create_viewer_and_token(db_session: Session, email: str = "ad-viewer@example.com") -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def _create_ad(db_session: Session) -> Ad:
    ad = Ad(
        advertiser_id=None,
        title="View Tracking Ad",
        video_url="https://example.com/view-tracking.mp4",
        reward_point=10,
        budget=100,
        remaining_budget=100,
        is_active=True,
    )
    db_session.add(ad)
    db_session.commit()
    db_session.refresh(ad)
    return ad


def test_start_creates_single_ad_view_record_per_user_and_ad(client, db_session: Session) -> None:
    viewer, token = _create_viewer_and_token(db_session)
    ad = _create_ad(db_session)

    first = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    second = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == 201
    assert second.status_code == 201

    ad_views = db_session.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == viewer.id).all()
    assert len(ad_views) == 1
    assert ad_views[0].completed_at is None
