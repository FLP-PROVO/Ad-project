from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User, UserRole
from app.schemas.ad_views import AdViewCreate, AdViewResponse


def test_ad_view_model_create_and_read(db_session: Session) -> None:
    viewer = User(email="model-viewer@example.com", password_hash="hash", role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Model Ad",
        video_url="https://example.com/model.mp4",
        reward_point=2,
        budget=20,
        remaining_budget=20,
        is_active=True,
    )
    db_session.add_all([viewer, ad])
    db_session.commit()

    start_time = datetime.now(timezone.utc)
    ad_view = AdView(
        ad_id=ad.id,
        viewer_id=viewer.id,
        started_at=start_time,
        completion_rate=Decimal("75.50"),
        watched_seconds=15,
        client_info={"user_agent": "pytest"},
    )
    db_session.add(ad_view)
    db_session.commit()
    db_session.refresh(ad_view)

    loaded = db_session.query(AdView).filter(AdView.id == ad_view.id).one()
    assert loaded.watched_seconds == 15
    assert loaded.completion_rate == Decimal("75.50")


def test_ad_view_schema_serialize_deserialize() -> None:
    payload = AdViewCreate(ad_id="6d12c2b5-e661-4e2a-9fb5-5f44e11a5caa", client_info={"ip_hash": "abc"})
    assert payload.client_info == {"ip_hash": "abc"}

    response = AdViewResponse(
        id="41df8344-782d-4f52-a6d7-6a35ef38ccaa",
        ad_id=payload.ad_id,
        viewer_id="2f3d850a-2724-4b30-8d8c-50cc372f4850",
        started_at=payload.started_at,
        completed_at=None,
        watched_seconds=None,
        completion_rate=None,
        rewarded=False,
        rewarded_points=0,
        client_info=payload.client_info,
        created_at=payload.started_at,
    )

    data = response.model_dump()
    assert data["ad_id"] == payload.ad_id
    assert data["rewarded"] is False
