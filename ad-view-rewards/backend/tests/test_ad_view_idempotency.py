from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.points_ledger import PointsLedger
from app.models.user import User, UserRole


def _setup(db_session: Session) -> tuple[User, str, Ad]:
    viewer = User(email="viewer-idempotent@example.com", password_hash=hash_password("pw"), role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Idempotent Ad",
        video_url="https://example.com/idempotent.mp4",
        file_path="/media/ads/idempotent.mp4",
        duration_seconds=30,
        reward_point=20,
        budget=20,
        remaining_budget=20,
        is_active=True,
        status="ready",
    )
    db_session.add_all([viewer, ad])
    db_session.commit()
    db_session.refresh(viewer)
    db_session.refresh(ad)
    return viewer, create_access_token(subject=viewer.email), ad


def test_complete_is_idempotent_and_daily_claim_is_blocked(client, db_session: Session) -> None:
    viewer, token, ad = _setup(db_session)

    start = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    view_id = start.json()["view_id"]

    first_complete = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id, "watched_seconds": 30},
    )
    assert first_complete.status_code == 200
    assert first_complete.json()["status"] == "rewarded"

    second_complete = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id, "watched_seconds": 30},
    )
    assert second_complete.status_code == 200
    assert second_complete.json()["status"] == "already_rewarded"

    second_start = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    second_view_id = second_start.json()["view_id"]
    second_view_complete = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": second_view_id, "watched_seconds": 30},
    )
    assert second_view_complete.status_code == 409
    assert second_view_complete.json()["detail"] == "already_claimed_today"

    ledger_entries = db_session.query(PointsLedger).filter(PointsLedger.user_id == viewer.id).all()
    assert len(ledger_entries) == 1
