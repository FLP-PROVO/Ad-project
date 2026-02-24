from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.ad import Ad
from app.models.user import User, UserRole
from app.routers import admin_ads
from app.services.storage_service import LocalStorageService


def _create_admin_token(db_session: Session) -> str:
    admin = User(
        email="admin-upload-too-large@example.com",
        password_hash=hash_password("secret-password"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=admin.email)


def test_upload_too_large_rejected_and_temp_deleted(client, db_session: Session, tmp_path, monkeypatch) -> None:
    admin_token = _create_admin_token(db_session)
    ad = Ad(
        title="Large file target",
        video_url="https://example.com/large.mp4",
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

    payload = b"x" * ((50 * 1024 * 1024) + 1)
    response = client.post(
        f"/api/v1/admin/ads/{ad.id}/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("large.mp4", payload, "video/mp4")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "file too large (max 50MB)"
    assert list(storage.tmp_dir.glob("*.upload")) == []
