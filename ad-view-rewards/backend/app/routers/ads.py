import uuid
import hashlib
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.points_ledger import PointsLedger
from app.services.ad_views_service import create_ad_view
from app.models.user import User
from app.schemas.ad import AdRead
from app.schemas.ad_views import AdViewResponse

router = APIRouter()


def _build_client_info(request: Request) -> dict[str, str | None]:
    client_ip = request.client.host if request.client else None
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip else None
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_hash": ip_hash,
    }


@router.get(
    "/available",
    response_model=list[AdRead],
    responses={
        200: {
            "description": "Active ads available for viewing",
            "content": {
                "application/json": {
                    "examples": {
                        "available_ads": {
                            "value": [
                                {
                                    "id": "2ffba427-9124-4965-b502-68a035ecf55a",
                                    "advertiser_id": "5fba7f47-b6d5-4ca9-a18a-b76266b6ee95",
                                    "title": "Gaming Headset Promo",
                                    "video_url": "https://example.com/video.mp4",
                                    "reward_point": 10,
                                    "budget": 100,
                                    "remaining_budget": 90,
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
def list_available_ads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AdRead]:
    del current_user
    ads = (
        db.query(Ad)
        .filter(Ad.is_active.is_(True), Ad.remaining_budget >= Ad.reward_point)
        .order_by(Ad.created_at.desc())
        .all()
    )
    return [AdRead.model_validate(ad) for ad in ads]


@router.post(
    "/{ad_id}/start",
    response_model=AdViewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Ad view started",
            "content": {
                "application/json": {
                    "examples": {
                        "started": {
                            "value": {
                                "id": "01c10ea3-18de-4caf-9f63-983f535dfdc0",
                                "ad_id": "2ffba427-9124-4965-b502-68a035ecf55a",
                                "viewer_id": "17cf3f5f-03bb-492a-bbc4-34a6ad4a4353",
                                "started_at": "2026-10-05T12:30:00Z",
                                "completed_at": None,
                                "watched_seconds": None,
                                "completion_rate": None,
                                "rewarded": False,
                                "rewarded_points": 0,
                                "client_info": {"user_agent": "Mozilla/5.0", "ip_hash": "abc"},
                                "created_at": "2026-10-05T12:30:00Z",
                            }
                        }
                    }
                }
            },
        }
    },
)
def start_ad_view(
    ad_id: Annotated[uuid.UUID, Path(examples=["2ffba427-9124-4965-b502-68a035ecf55a"])],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdViewResponse:
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None or not ad.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active ad not found")

    existing = db.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == current_user.id).first()
    if existing:
        return AdViewResponse.model_validate(existing)

    try:
        ad_view = create_ad_view(db, ad.id, current_user.id, _build_client_info(request))
    except IntegrityError:
        db.rollback()
        ad_view = db.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == current_user.id).first()
        if ad_view is None:
            raise
        return AdViewResponse.model_validate(ad_view)

    return AdViewResponse.model_validate(ad_view)


@router.post(
    "/{ad_id}/complete",
    response_model=AdViewResponse,
    responses={
        200: {
            "description": "Ad view completed and reward granted if eligible",
            "content": {
                "application/json": {
                    "examples": {
                        "completed": {
                            "value": {
                                "id": "01c10ea3-18de-4caf-9f63-983f535dfdc0",
                                "ad_id": "2ffba427-9124-4965-b502-68a035ecf55a",
                                "viewer_id": "17cf3f5f-03bb-492a-bbc4-34a6ad4a4353",
                                "started_at": "2026-10-05T12:30:00Z",
                                "completed_at": "2026-10-05T12:31:00Z",
                                "watched_seconds": None,
                                "completion_rate": None,
                                "rewarded": True,
                                "rewarded_points": 10,
                                "client_info": {"user_agent": "Mozilla/5.0", "ip_hash": "abc"},
                                "created_at": "2026-10-05T12:30:00Z",
                            }
                        }
                    }
                }
            },
        }
    },
)
def complete_ad_view(
    ad_id: Annotated[uuid.UUID, Path(examples=["2ffba427-9124-4965-b502-68a035ecf55a"])],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdViewResponse:
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None or not ad.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active ad not found")

    ad_view = db.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == current_user.id).first()
    if ad_view is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad view not started")

    now = datetime.now(timezone.utc)
    with db.begin_nested():
        ad = db.query(Ad).filter(Ad.id == ad.id).with_for_update().one()
        ad_view = db.query(AdView).filter(AdView.id == ad_view.id).with_for_update().one()

        if ad_view.completed_at is None:
            ad_view.completed_at = now

        if not ad_view.rewarded:
            if ad.remaining_budget < ad.reward_point:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient ad budget")

            ledger_entry = PointsLedger(
                user_id=current_user.id,
                change=ad.reward_point,
                reason="ad_reward",
                reference_id=ad_view.id,
            )
            db.add(ledger_entry)
            ad.remaining_budget -= ad.reward_point
            ad_view.rewarded = True
            ad_view.rewarded_points = ad.reward_point

    db.commit()
    db.refresh(ad_view)
    return AdViewResponse.model_validate(ad_view)
