from urllib.parse import parse_qs, urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.routers import media_stream
from app.services.storage_service import LocalStorageService


SAMPLE_MP4_BYTES = b"\x00\x00\x00\x20ftypisom\x00\x00\x00\x01isomiso2avc1mp41"


def _create_viewer_with_token(db_session: Session, email: str) -> tuple[User, str]:
    viewer = User(email=email, password_hash=hash_password("secret-password"), role=UserRole.viewer)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    return viewer, create_access_token(subject=viewer.email)


def test_tampered_signature_is_rejected(client, db_session: Session, tmp_path, monkeypatch) -> None:
    settings.base_url = "http://testserver"
    settings.secret_key = "test-secret"
    storage = LocalStorageService(base_dir=tmp_path / "media", tmp_dir=tmp_path / "tmp")
    monkeypatch.setattr(media_stream, "LocalStorageService", lambda: storage)

    viewer, token = _create_viewer_with_token(db_session, email="viewer-stream@example.com")
    media_file = storage.base_dir / "ads" / "sample.mp4"
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_bytes(SAMPLE_MP4_BYTES)

    signed_url = storage.generate_signed_url("/media/ads/sample.mp4", viewer.id, expires_seconds=300)
    parsed = urlparse(signed_url)
    signed_token = parse_qs(parsed.query)["token"][0]
    tampered = f"{signed_token[:-1]}0"

    response = client.get(f"{parsed.path}?token={tampered}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_token_bound_to_user_is_rejected_for_other_user(client, db_session: Session, tmp_path, monkeypatch) -> None:
    settings.base_url = "http://testserver"
    settings.secret_key = "test-secret"
    storage = LocalStorageService(base_dir=tmp_path / "media", tmp_dir=tmp_path / "tmp")
    monkeypatch.setattr(media_stream, "LocalStorageService", lambda: storage)

    owner, _ = _create_viewer_with_token(db_session, email="owner@example.com")
    _, intruder_token = _create_viewer_with_token(db_session, email="intruder@example.com")
    media_file = storage.base_dir / "ads" / "sample.mp4"
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_bytes(SAMPLE_MP4_BYTES)

    signed_url = storage.generate_signed_url("/media/ads/sample.mp4", owner.id, expires_seconds=300)
    parsed = urlparse(signed_url)

    response = client.get(parsed.path + "?" + parsed.query, headers={"Authorization": f"Bearer {intruder_token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
