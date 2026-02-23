import uuid
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.ad import Ad
from app.models.ad_view import AdView
from app.models.points_ledger import PointsLedger
from app.models.user import User
from app.schemas.ad_view import AdViewRead

router = APIRouter()


def _build_client_info(request: Request) -> dict[str, str | None]:
    client_ip = request.client.host if request.client else None
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip else None
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_hash": ip_hash,
    }


@router.post("/{ad_id}/start", response_model=AdViewRead, status_code=status.HTTP_201_CREATED)
def start_ad_view(
    ad_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdViewRead:
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad is None or not ad.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active ad not found")

    existing = db.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == current_user.id).first()
    if existing:
        return AdViewRead.model_validate(existing)

    ad_view = AdView(
        ad_id=ad.id,
        viewer_id=current_user.id,
        started_at=datetime.now(timezone.utc),
        completed=False,
        reward_granted=False,
        client_info=_build_client_info(request),
    )
    db.add(ad_view)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        ad_view = db.query(AdView).filter(AdView.ad_id == ad.id, AdView.viewer_id == current_user.id).first()
        if ad_view is None:
            raise
        return AdViewRead.model_validate(ad_view)

    db.refresh(ad_view)
    return AdViewRead.model_validate(ad_view)


@router.post("/{ad_id}/complete", response_model=AdViewRead)
def complete_ad_view(
    ad_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdViewRead:
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

        if not ad_view.completed:
            ad_view.completed = True
            ad_view.completed_at = now

        if ad_view.completed and not ad_view.reward_granted:
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
            ad_view.reward_granted = True

    db.commit()
    db.refresh(ad_view)
    return AdViewRead.model_validate(ad_view)
