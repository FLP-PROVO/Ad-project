import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.points_ledger import PointsLedger

logger = logging.getLogger(__name__)


class RewardProcessingError(RuntimeError):
    """Raised when reward processing unexpectedly fails."""


class InsufficientWatchTimeError(RuntimeError):
    def __init__(self, required_seconds: int) -> None:
        self.required_seconds = required_seconds
        super().__init__("insufficient_watch_time")


def required_seconds_for_ad(ad: Ad) -> int:
    if ad.duration_seconds is None:
        return 15
    return max(15, int(ad.duration_seconds * 0.8))


def _completion_rate(watched_seconds: int, duration_seconds: int | None) -> Decimal | None:
    if duration_seconds is None or duration_seconds <= 0:
        return None
    rate = Decimal(watched_seconds * 100) / Decimal(duration_seconds)
    return rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def process_ad_reward(
    db: Session,
    *,
    ad_id: uuid.UUID,
    view_id: uuid.UUID,
    viewer_id: uuid.UUID,
    watched_seconds: int,
) -> tuple[str, int, int]:
    now = datetime.now(timezone.utc)

    ad_view = db.query(AdView).filter(AdView.id == view_id).first()
    if ad_view is None or ad_view.ad_id != ad_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ad_view_not_found")
    if ad_view.viewer_id != viewer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    ad = db.query(Ad).filter(Ad.id == ad_id, Ad.status == "ready", Ad.is_active.is_(True)).first()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ad_not_found")

    if ad_view.rewarded:
        new_balance = db.query(func.coalesce(func.sum(PointsLedger.change), 0)).filter(PointsLedger.user_id == viewer_id).scalar()
        return "already_rewarded", ad_view.rewarded_points, int(new_balance or 0)

    required_seconds = required_seconds_for_ad(ad)
    if watched_seconds < required_seconds:
        ad_view.watched_seconds = watched_seconds
        ad_view.completed_at = ad_view.completed_at or now
        ad_view.completion_rate = _completion_rate(watched_seconds, ad.duration_seconds)
        db.commit()
        raise InsufficientWatchTimeError(required_seconds)

    already_claimed_today = (
        db.query(AdView)
        .filter(
            AdView.viewer_id == viewer_id,
            AdView.ad_id == ad_id,
            AdView.rewarded.is_(True),
            func.date(AdView.created_at) == func.current_date(),
            AdView.id != ad_view.id,
        )
        .first()
    )
    if already_claimed_today:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already_claimed_today")

    try:
        with db.begin_nested():
            locked_ad = db.query(Ad).filter(Ad.id == ad_id).with_for_update().one()
            locked_view = db.query(AdView).filter(AdView.id == view_id).with_for_update().one()

            if locked_view.rewarded:
                new_balance = (
                    db.query(func.coalesce(func.sum(PointsLedger.change), 0)).filter(PointsLedger.user_id == viewer_id).scalar()
                )
                result = ("already_rewarded", locked_view.rewarded_points, int(new_balance or 0))
            else:

                if locked_ad.remaining_budget < locked_ad.reward_point:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="insufficient_budget")

                db.add(
                    PointsLedger(
                        user_id=viewer_id,
                        change=locked_ad.reward_point,
                        reason="ad_reward",
                        reference_id=locked_view.id,
                    )
                )
                locked_view.rewarded = True
                locked_view.rewarded_points = locked_ad.reward_point
                locked_view.watched_seconds = watched_seconds
                locked_view.completed_at = now
                locked_view.completion_rate = _completion_rate(watched_seconds, locked_ad.duration_seconds)
                locked_ad.remaining_budget -= locked_ad.reward_point
                db.flush()

                new_balance = db.query(func.coalesce(func.sum(PointsLedger.change), 0)).filter(PointsLedger.user_id == viewer_id).scalar()
                result = ("rewarded", locked_ad.reward_point, int(new_balance or 0))

        db.commit()
        return result
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Reward duplicate/consistency error ad=%s view=%s user=%s", ad_id, view_id, viewer_id)
        refreshed_view = db.query(AdView).filter(AdView.id == view_id).first()
        if refreshed_view is not None and refreshed_view.rewarded:
            new_balance = db.query(func.coalesce(func.sum(PointsLedger.change), 0)).filter(PointsLedger.user_id == viewer_id).scalar()
            return "already_rewarded", refreshed_view.rewarded_points, int(new_balance or 0)
        raise RewardProcessingError("reward processing failed") from exc
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise RewardProcessingError("reward processing failed") from exc
