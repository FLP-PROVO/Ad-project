import uuid

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.points_ledger import PointsLedger
from app.models.user import User, UserRole


def _seed(client, db_session: Session) -> tuple[str, Ad, str, str]:
    viewer = User(email="viewer-concurrency@example.com", password_hash=hash_password("pw"), role=UserRole.viewer)
    ad = Ad(
        advertiser_id=None,
        title="Concurrency Ad",
        video_url="https://example.com/concurrency.mp4",
        file_path="/media/ads/concurrency.mp4",
        duration_seconds=30,
        reward_point=10,
        budget=10,
        remaining_budget=10,
        is_active=True,
        status="ready",
    )
    db_session.add_all([viewer, ad])
    db_session.commit()
    token = create_access_token(subject=viewer.email)

    start1 = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    start2 = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    return token, ad, start1.json()["view_id"], start2.json()["view_id"]


def test_budget_allows_only_one_reward_across_two_views(client, db_session: Session) -> None:
    token, ad, view_id_1, view_id_2 = _seed(client, db_session)

    first = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id_1, "watched_seconds": 30},
    )
    second = client.post(
        f"/api/v1/ads/{ad.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"view_id": view_id_2, "watched_seconds": 30},
    )

    assert first.status_code == 200
    assert first.json()["status"] == "rewarded"
    assert second.status_code == 409
    assert second.json()["detail"] in {"already_claimed_today", "insufficient_budget"}

    ledger_count = db_session.query(PointsLedger).count()
    assert ledger_count == 1
    db_session.refresh(ad)
    assert ad.remaining_budget == 0
    assert ad.remaining_budget >= 0


def test_transaction_rolls_back_when_ledger_insert_fails(client, db_session: Session) -> None:
    token, ad, view_id, _ = _seed(client, db_session)

    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    event.listen(PointsLedger, "before_insert", _raise)
    try:
        response = client.post(
            f"/api/v1/ads/{ad.id}/complete",
            headers={"Authorization": f"Bearer {token}"},
            json={"view_id": view_id, "watched_seconds": 30},
        )
    finally:
        event.remove(PointsLedger, "before_insert", _raise)

    assert response.status_code == 500

    db_session.refresh(ad)
    ad_view = db_session.query(AdView).filter(AdView.id == uuid.UUID(view_id)).one()
    assert ad.remaining_budget == 10
    assert ad_view.rewarded is False
    assert db_session.query(PointsLedger).count() == 0
