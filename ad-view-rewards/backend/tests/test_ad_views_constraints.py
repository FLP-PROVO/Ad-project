from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User, UserRole


def test_daily_unique_constraint_prevents_duplicate_reward_window(db_session: Session) -> None:
    viewer = User(email="dup-viewer@example.com", password_hash="hash", role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Uniq Ad",
        video_url="https://example.com/uniq.mp4",
        reward_point=1,
        budget=10,
        remaining_budget=10,
        is_active=True,
    )
    db_session.add_all([viewer, ad])
    db_session.commit()

    now = datetime.now(timezone.utc)
    first = AdView(ad_id=ad.id, viewer_id=viewer.id, started_at=now, created_at=now)
    second = AdView(ad_id=ad.id, viewer_id=viewer.id, started_at=now, created_at=now)

    db_session.add(first)
    db_session.commit()

    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.commit()
