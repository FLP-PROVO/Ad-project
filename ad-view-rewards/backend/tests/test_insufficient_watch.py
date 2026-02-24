import uuid
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User, UserRole


def test_insufficient_watch_time_returns_400(client, db_session: Session) -> None:
    viewer = User(email="viewer-short@example.com", password_hash=hash_password("pw"), role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Short Watch Ad",
        video_url="https://example.com/short.mp4",
        file_path="/media/ads/short.mp4",
        duration_seconds=40,
        reward_point=10,
        budget=30,
        remaining_budget=30,
        is_active=True,
        status="ready",
    )
    db_session.add_all([viewer, ad])
    db_session.commit()
    token = create_access_token(subject=viewer.email)

    start = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    view_id = start.json()["view_id"]

    complete = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id, "watched_seconds": 20},
    )
    assert complete.status_code == 400
    assert complete.json()["detail"] == "insufficient_watch_time"
    assert complete.json()["required_seconds"] == 32

    ad_view = db_session.query(AdView).filter(AdView.id == uuid.UUID(view_id)).one()
    assert ad_view.rewarded is False
