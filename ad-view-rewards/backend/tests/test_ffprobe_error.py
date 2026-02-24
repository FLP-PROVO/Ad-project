from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import admin_ads
from app.services.media_processing import MediaProcessingError
from app.services.storage_service import LocalStorageService


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin-upload-ffprobe-error@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_ffprobe_error_returns_500_and_marks_ad_failed(client, db_session: Session, tmp_path, monkeypatch) -> None:
    admin_token = _create_admin_token(db_session)
    ad = Ad(
        title="ffprobe fail target",
        video_url="https://example.com/fail.mp4",
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

    def _raise_error(_: object) -> int:
        raise MediaProcessingError("ffprobe failed or invalid video file")

    monkeypatch.setattr(admin_ads, "probe_video_duration_seconds", _raise_error)

    response = client.post(
        f"/api/v1/admin/ads/{ad.id}/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("broken.mp4", b"broken-content", "video/mp4")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "ffprobe failed or invalid video file"

    db_session.expire_all()
    stored_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert stored_ad is not None
    assert stored_ad.status == "failed"
    assert list(storage.tmp_dir.glob("*.upload")) == []
