import uuid

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import admin_ads
from app.services.storage_service import LocalStorageService


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin-upload-valid@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_upload_valid_mp4_updates_ad_and_persists_file(client, db_session: Session, tmp_path, monkeypatch) -> None:
    admin_token = _create_admin_token(db_session)
    ad = Ad(
        title="Upload target",
        video_url="https://example.com/upload.mp4",
        reward_point=10,
        budget=100,
        remaining_budget=100,
        is_active=True,
        status="uploading",
    )
    db_session.add(ad)
    db_session.commit()

    storage = LocalStorageService(base_dir=tmp_path / "media", tmp_dir=tmp_path / "tmp")
    monkeypatch.setattr(admin_ads, "LocalStorageService", lambda: storage)
    monkeypatch.setattr(admin_ads, "probe_video_duration_seconds", lambda _: 30)

    response = client.post(
        f"/api/v1/admin/ads/{ad.id}/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("sample.mp4", b"valid-mp4-content", "video/mp4")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(ad.id)
    assert body["status"] == "ready"
    assert body["duration_seconds"] == 30
    assert body["file_size_bytes"] == len(b"valid-mp4-content")
    assert body["file_path"].startswith("/media/ads/")

    db_session.expire_all()
    stored_ad = db_session.query(Ad).filter(Ad.id == uuid.UUID(body["id"])).first()
    assert stored_ad is not None
    assert stored_ad.status == "ready"
    assert stored_ad.duration_seconds == 30
    assert stored_ad.file_size_bytes == len(b"valid-mp4-content")
    assert stored_ad.file_path is not None

    saved_relative_path = stored_ad.file_path.removeprefix("/media/")
    saved_path = storage.base_dir / saved_relative_path
    assert saved_path.exists()
    assert list(storage.tmp_dir.glob("*.upload")) == []
