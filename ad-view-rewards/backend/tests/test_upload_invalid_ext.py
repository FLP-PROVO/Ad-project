from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import admin_ads
from app.services.storage_service import LocalStorageService


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin-upload-invalid-ext@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_upload_non_mp4_extension_rejected(client, db_session: Session, tmp_path, monkeypatch) -> None:
    admin_token = _create_admin_token(db_session)
    ad = Ad(
        title="Invalid ext target",
        video_url="https://example.com/invalid.mov",
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

    response = client.post(
        f"/api/v1/admin/ads/{ad.id}/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("not-mp4.txt", b"plain-text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid file extension (only .mp4)"
    assert not storage.tmp_dir.exists() or list(storage.tmp_dir.glob("*.upload")) == []
