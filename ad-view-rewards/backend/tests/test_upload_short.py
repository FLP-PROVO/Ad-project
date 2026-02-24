from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import admin_ads
from app.services.storage_service import LocalStorageService


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin-upload-short@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_upload_short_mp4_marks_failed_and_no_persisted_file(client, db_session: Session, tmp_path, monkeypatch) -> None:
    admin_token = _create_admin_token(db_session)
    ad = Ad(
        title="Short upload target",
        video_url="https://example.com/short.mp4",
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
    monkeypatch.setattr(admin_ads, "probe_video_duration_seconds", lambda _: 10)

    response = client.post(
        f"/api/v1/admin/ads/{ad.id}/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("short.mp4", b"short-content", "video/mp4")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "video too short (min 15 seconds)"

    db_session.expire_all()
    stored_ad = db_session.query(Ad).filter(Ad.id == ad.id).first()
    assert stored_ad is not None
    assert stored_ad.status == "failed"
    assert stored_ad.file_path is None

    assert not storage.base_dir.exists() or list(storage.base_dir.rglob("*.mp4")) == []
    assert list(storage.tmp_dir.glob("*.upload")) == []
