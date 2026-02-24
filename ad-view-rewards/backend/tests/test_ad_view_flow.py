import uuid
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.points_ledger import PointsLedger
from app.models.user import User, UserRole


def _create_viewer_with_token(db_session: Session, email: str = "viewer-flow@example.com") -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def _create_ad(db_session: Session, reward_point: int = 10, budget: int = 100, duration_seconds: int | None = 30) -> Ad:
    ad = Ad(
        advertiser_id=None,
        title="Rewarded Ad",
        video_url="https://example.com/rewarded.mp4",
        file_path="/media/ads/rewarded.mp4",
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


def test_start_then_complete_creates_ledger_and_decrements_budget(client, db_session: Session) -> None:
    viewer, token = _create_viewer_with_token(db_session)
    ad = _create_ad(db_session, reward_point=15, budget=100, duration_seconds=20)

    start_response = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert start_response.status_code == 201
    view_id = start_response.json()["view_id"]

    complete_response = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id, "watched_seconds": 20},
    )
    assert complete_response.status_code == 200
    complete_body = complete_response.json()
    assert complete_body["status"] == "rewarded"
    assert complete_body["rewarded_points"] == 15
    assert complete_body["new_balance"] == 15

    ledger_entries = db_session.query(PointsLedger).filter(PointsLedger.user_id == viewer.id).all()
    assert len(ledger_entries) == 1

    db_session.expire_all()
    updated_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    ad_view = db_session.query(AdView).filter(AdView.id == uuid.UUID(view_id)).first()
    assert updated_ad is not None
    assert updated_ad.remaining_budget == 85
    assert ad_view is not None
    assert ad_view.rewarded is True
