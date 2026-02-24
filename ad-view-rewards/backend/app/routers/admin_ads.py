from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db.base import get_db
from app.models.ad import Ad
from app.models.user import User
from app.schemas.ad import AdCreate, AdRead

router = APIRouter()


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
