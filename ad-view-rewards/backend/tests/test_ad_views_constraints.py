from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User, UserRole


def test_multiple_views_same_day_can_be_recorded(db_session: Session) -> None:
    viewer = User(email="dup-viewer@example.com", password_hash="hash", role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Uniq Ad",
        video_url="https://example.com/uniq.mp4",
        reward_point=1,
        budget=10,
        remaining_budget=10,
        is_active=True,
        status="ready",
    )
    db_session.add_all([viewer, ad])
    db_session.commit()

    now = datetime.now(timezone.utc)
    first = AdView(ad_id=ad.id, viewer_id=viewer.id, started_at=now, created_at=now)
    second = AdView(ad_id=ad.id, viewer_id=viewer.id, started_at=now, created_at=now)

    db_session.add_all([first, second])
    db_session.commit()

    count = db_session.query(AdView).filter(AdView.viewer_id == viewer.id, AdView.ad_id == ad.id).count()
    assert count == 2
