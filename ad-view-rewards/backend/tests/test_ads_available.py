from urllib.parse import parse_qs, urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import ads, media_stream
from app.services.storage_service import LocalStorageService


SAMPLE_MP4_BYTES = b"\x00\x00\x00\x20ftypisom\x00\x00\x00\x01isomiso2avc1mp41"


def _create_viewer_with_token(db_session: Session, email: str) -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def test_available_ads_includes_signed_video_url(client, db_session: Session, tmp_path, monkeypatch) -> None:
    settings.base_url = "http://testserver"
    settings.secret_key = "test-secret"

    storage = LocalStorageService(base_dir=tmp_path / "media", tmp_dir=tmp_path / "tmp")
    monkeypatch.setattr(ads, "LocalStorageService", lambda: storage)
    monkeypatch.setattr(media_stream, "LocalStorageService", lambda: storage)

    viewer, token = _create_viewer_with_token(db_session, email="viewer-available@example.com")
    media_file = storage.base_dir / "ads" / "sample.mp4"
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_bytes(SAMPLE_MP4_BYTES)

    eligible_ad = Ad(
        title="Eligible ad",
        video_url="https://example.com/rewarded.mp4",
        file_path="/media/ads/sample.mp4",
        duration_seconds=30,
        reward_point=10,
        budget=50,
        remaining_budget=50,
        status="ready",
        is_active=True,
    )
    db_session.add(eligible_ad)
    db_session.commit()

    response = client.get("/api/v1/ads/available", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(eligible_ad.id)
    assert body[0]["duration_seconds"] == 30
    parsed = urlparse(body[0]["video_url"])
    params = parse_qs(parsed.query)
    assert parsed.path == "/media/ads/sample.mp4"
    assert "token" in params
    assert params["token"][0]

    stream_response = client.get(
        body[0]["video_url"],
        headers={"Authorization": f"Bearer {create_access_token(subject=viewer.email)}"},
    )
    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"] == "video/mp4"
