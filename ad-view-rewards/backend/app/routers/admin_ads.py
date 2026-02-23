from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.db.base import get_db
from app.models.ad import Ad
from app.models.user import User
from app.schemas.ad import AdCreate, AdRead

router = APIRouter()


@router.post("/ads", response_model=AdRead, status_code=status.HTTP_201_CREATED)
def create_ad(
    payload: AdCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdRead:
    ad = Ad(
        advertiser_id=payload.advertiser_id,
        title=payload.title,
        video_url=payload.video_url,
        reward_point=payload.reward_point,
        budget=payload.budget,
        remaining_budget=payload.budget,
        is_active=payload.is_active,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return AdRead.model_validate(ad)


@router.get("/ads", response_model=list[AdRead])
def list_ads(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> list[AdRead]:
    ads = db.query(Ad).order_by(Ad.created_at.desc()).all()
    return [AdRead.model_validate(ad) for ad in ads]
