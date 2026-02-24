import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, status
from fastapi import File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db.base import get_db
from app.models.ad import Ad
from app.models.user import User
from app.schemas.ad import AdCreate, AdRead
from app.services.media_processing import MediaProcessingError, probe_video_duration_seconds
from app.services.storage_service import LocalStorageService

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
MIN_DURATION_SECONDS = 15


@router.post(
    "/ads",
    response_model=AdRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Ad created",
            "content": {
                "application/json": {
                    "examples": {
                        "created": {
                            "value": {
                                "id": "2ffba427-9124-4965-b502-68a035ecf55a",
                                "advertiser_id": "5fba7f47-b6d5-4ca9-a18a-b76266b6ee95",
                                "title": "Gaming Headset Promo",
                                "video_url": "https://example.com/video.mp4",
                                "file_path": None,
                                "duration_seconds": None,
                                "file_size_bytes": None,
                                "status": "uploading",
                                "reward_point": 10,
                                "budget": 100,
                                "remaining_budget": 100,
                                "is_active": True,
                                "created_at": "2026-10-05T12:00:00Z",
                            }
                        }
                    }
                }
            },
        }
    },
)
def create_ad(
    payload: AdCreate = Body(
        ...,
        examples=[
            {
                "advertiser_id": "5fba7f47-b6d5-4ca9-a18a-b76266b6ee95",
                "title": "Gaming Headset Promo",
                "video_url": "https://example.com/video.mp4",
                "reward_point": 10,
                "budget": 100,
                "is_active": True,
            }
        ],
    ),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdRead:
    ad = Ad(
        advertiser_id=payload.advertiser_id,
        title=payload.title,
        video_url=payload.video_url,
        file_path=None,
        duration_seconds=None,
        file_size_bytes=None,
        status="uploading",
        reward_point=payload.reward_point,
        budget=payload.budget,
        remaining_budget=payload.budget,
        is_active=payload.is_active,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return AdRead.model_validate(ad)


@router.get(
    "/ads",
    response_model=list[AdRead],
    responses={
        200: {
            "description": "Admin ad list",
            "content": {
                "application/json": {
                    "examples": {
                        "ads": {
                            "value": [
                                {
                                    "id": "2ffba427-9124-4965-b502-68a035ecf55a",
                                    "advertiser_id": "5fba7f47-b6d5-4ca9-a18a-b76266b6ee95",
                                    "title": "Gaming Headset Promo",
                                    "video_url": "https://example.com/video.mp4",
                                    "file_path": None,
                                    "duration_seconds": None,
                                    "file_size_bytes": None,
                                    "status": "uploading",
                                    "reward_point": 10,
                                    "budget": 100,
                                    "remaining_budget": 100,
                                    "is_active": True,
                                    "created_at": "2026-10-05T12:00:00Z",
                                }
                            ]
                        }
                    }
                }
            },
        }
    },
)
def list_ads(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[AdRead]:
    ads = db.query(Ad).order_by(Ad.created_at.desc()).all()
    return [AdRead.model_validate(ad) for ad in ads]


@router.post(
    "/ads/{ad_id}/upload",
    response_model=AdRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_ad_video(
    ad_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdRead:
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ad not found")

    if file.filename is None or Path(file.filename).suffix.lower() != ".mp4":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid file extension (only .mp4)")
    if file.content_type not in {"video/mp4", "application/octet-stream"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid content type (expected video/mp4)")

    storage = LocalStorageService()
    tmp_path: Path | None = None

    try:
        file_bytes = file.file.read()
        tmp_path = storage.save_temp(file_bytes, file.filename)

        file_size_bytes = tmp_path.stat().st_size
        if file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
            storage.delete_if_exists(tmp_path)
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large (max 50MB)")

        try:
            duration_seconds = probe_video_duration_seconds(tmp_path)
        except MediaProcessingError as exc:
            ad.status = "failed"
            db.commit()
            storage.delete_if_exists(tmp_path)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        if duration_seconds < MIN_DURATION_SECONDS:
            ad.status = "failed"
            db.commit()
            storage.delete_if_exists(tmp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="video too short (min 15 seconds)",
            )

        destination_relative_path = Path("ads") / f"{uuid.uuid4()}.mp4"
        storage.finalize(tmp_path, destination_relative_path)

        ad.file_path = f"/media/{destination_relative_path.as_posix()}"
        ad.duration_seconds = duration_seconds
        ad.file_size_bytes = file_size_bytes
        ad.status = "ready"
        db.commit()
        db.refresh(ad)
        return AdRead.model_validate(ad)
    finally:
        if tmp_path is not None and tmp_path.exists():
            storage.delete_if_exists(tmp_path)
