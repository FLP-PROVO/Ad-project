from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.ad_view import AdView
from app.models.points_ledger import PointsLedger
from app.models.user import User, UserRole


def _create_viewer_with_token(db_session: Session, email: str = "viewer-reward@example.com") -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def _create_ad(db_session: Session, reward_point: int = 10, budget: int = 100) -> Ad:
    ad = Ad(
        advertiser_id=None,
        title="Rewarded Ad",
        video_url="https://example.com/rewarded.mp4",
        reward_point=reward_point,
        budget=budget,
        remaining_budget=budget,
        is_active=True,
    )
    db_session.add(ad)
    db_session.commit()
    db_session.refresh(ad)
    return ad


def test_start_then_complete_creates_ledger_and_decrements_budget(client, db_session: Session) -> None:
    viewer, token = _create_viewer_with_token(db_session)
    ad = _create_ad(db_session, reward_point=15, budget=100)

    start_response = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert start_response.status_code == 201
    start_body = start_response.json()
    assert start_body["completed"] is False
    assert start_body["reward_granted"] is False

    complete_response = client.post(f"/api/v1/ads/{ad.id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert complete_response.status_code == 200
    complete_body = complete_response.json()
    assert complete_body["completed"] is True
    assert complete_body["reward_granted"] is True

    ledger_entries = db_session.query(PointsLedger).filter(PointsLedger.user_id == viewer.id).all()
    assert len(ledger_entries) == 1
    assert ledger_entries[0].change == 15
    assert ledger_entries[0].reason == "ad_reward"

    updated_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert updated_ad is not None
    assert updated_ad.remaining_budget == 85


def test_complete_is_idempotent_and_does_not_duplicate_reward(client, db_session: Session) -> None:
    viewer, token = _create_viewer_with_token(db_session)
    ad = _create_ad(db_session, reward_point=20, budget=100)

    start_response = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert start_response.status_code == 201

    first_complete = client.post(f"/api/v1/ads/{ad.id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert first_complete.status_code == 200
    second_complete = client.post(f"/api/v1/ads/{ad.id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert second_complete.status_code == 200

    ledger_entries = db_session.query(PointsLedger).filter(PointsLedger.user_id == viewer.id).all()
    assert len(ledger_entries) == 1

    updated_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert updated_ad is not None
    assert updated_ad.remaining_budget == 80


def test_same_user_cannot_claim_same_ad_reward_twice(client, db_session: Session) -> None:
    viewer, token = _create_viewer_with_token(db_session)
    ad = _create_ad(db_session, reward_point=5, budget=100)

    first_start = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert first_start.status_code == 201
    second_start = client.post(f"/api/v1/ads/{ad.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert second_start.status_code == 201

    first_complete = client.post(f"/api/v1/ads/{ad.id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert first_complete.status_code == 200
    second_complete = client.post(f"/api/v1/ads/{ad.id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert second_complete.status_code == 200

    ad_views = db_session.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == viewer.id).all()
    assert len(ad_views) == 1
    assert ad_views[0].reward_granted is True

    ledger_entries = db_session.query(PointsLedger).filter(PointsLedger.user_id == viewer.id).all()
    assert len(ledger_entries) == 1
