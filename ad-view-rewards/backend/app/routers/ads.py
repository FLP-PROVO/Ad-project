import hashlib
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_viewer
from app.db.base import get_db
from app.models.ad import Ad
from app.models.ad_views import AdView
from app.models.user import User
from app.schemas.ad import AdAvailableRead
from app.schemas.ad_views import AdViewCompleteRequest, AdViewCompleteResponse, AdViewStartResponse
from app.services.ad_views_service import create_ad_view
from app.services.rewards import InsufficientWatchTimeError, RewardProcessingError, process_ad_reward
from app.services.storage_service import LocalStorageService

router = APIRouter()
logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.time()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window_seconds:
                q.popleft()
            if len(q) >= self.limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limit_exceeded")
            q.append(now)


start_rate_limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
complete_rate_limiter = InMemoryRateLimiter(limit=10, window_seconds=60)


def _build_client_info(request: Request) -> dict[str, str | None]:
    client_ip = request.client.host if request.client else None
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip else None
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_hash": ip_hash,
    }


def _log_suspicious_complete(db: Session, user_id: uuid.UUID, ad_id: uuid.UUID, ip_hash: str | None) -> None:
    recent_user_completes = (
        db.query(AdView)
        .filter(AdView.viewer_id == user_id, AdView.rewarded.is_(True))
        .order_by(AdView.created_at.desc())
        .limit(5)
        .count()
    )
    if recent_user_completes >= 5:
        logger.warning("suspicious_complete_burst user=%s ad=%s ip_hash=%s", user_id, ad_id, ip_hash)

    if ip_hash:
        recent_views = db.query(AdView.viewer_id, AdView.client_info).order_by(AdView.created_at.desc()).limit(200).all()
        same_ip_accounts = len({viewer for viewer, info in recent_views if (info or {}).get("ip_hash") == ip_hash})
        if same_ip_accounts >= 3:
            logger.warning("suspicious_same_ip_multi_account user=%s ad=%s ip_hash=%s", user_id, ad_id, ip_hash)


@router.get("/available", response_model=list[AdAvailableRead])
def list_available_ads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_viewer),
) -> list[AdAvailableRead]:
    ads = (
        db.query(Ad)
        .filter(
            Ad.status == "ready",
            Ad.is_active.is_(True),
            Ad.remaining_budget >= Ad.reward_point,
            Ad.file_path.is_not(None),
            Ad.duration_seconds.is_not(None),
        )
        .order_by(Ad.created_at.desc())
        .all()
    )

    storage = LocalStorageService()
    return [
        AdAvailableRead(
            id=ad.id,
            title=ad.title,
            reward_point=ad.reward_point,
            duration_seconds=ad.duration_seconds,
            video_url=storage.generate_signed_url(ad.file_path, current_user.id, expires_seconds=300),
        )
        for ad in ads
        if ad.file_path is not None and ad.duration_seconds is not None
    ]


@router.post("/{ad_id}/start", response_model=AdViewStartResponse, status_code=status.HTTP_201_CREATED)
def start_ad_view(
    ad_id: Annotated[uuid.UUID, Path(examples=["2ffba427-9124-4965-b502-68a035ecf55a"])],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_viewer),
) -> AdViewStartResponse:
    start_rate_limiter.check(f"start:{current_user.id}")

    ad = db.query(Ad).filter(Ad.id == ad_id, Ad.status == "ready", Ad.is_active.is_(True)).first()
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ad_not_found")

    ad_view = create_ad_view(db, ad.id, current_user.id, _build_client_info(request))
    return AdViewStartResponse(view_id=ad_view.id, started_at=ad_view.started_at)


@router.post("/{ad_id}/complete", response_model=AdViewCompleteResponse)
def complete_ad_view(
    ad_id: Annotated[uuid.UUID, Path(examples=["2ffba427-9124-4965-b502-68a035ecf55a"])],
    payload: AdViewCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_viewer),
) -> AdViewCompleteResponse | JSONResponse:
    complete_rate_limiter.check(f"complete:{current_user.id}")

    client_info = _build_client_info(request)
    _log_suspicious_complete(db, current_user.id, ad_id, client_info.get("ip_hash"))

    try:
        status_text, rewarded_points, new_balance = process_ad_reward(
            db,
            ad_id=ad_id,
            view_id=payload.view_id,
            viewer_id=current_user.id,
            watched_seconds=payload.watched_seconds,
        )
    except InsufficientWatchTimeError as exc:
        logger.info(
            "insufficient_watch_time user=%s ad=%s ip_hash=%s required_seconds=%s",
            current_user.id,
            ad_id,
            client_info.get("ip_hash"),
            exc.required_seconds,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "insufficient_watch_time", "required_seconds": exc.required_seconds},
        )
    except RewardProcessingError as exc:
        logger.exception(
            "reward_processing_failed user=%s ad=%s ip_hash=%s",
            current_user.id,
            ad_id,
            client_info.get("ip_hash"),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="server_error") from exc

    return AdViewCompleteResponse(status=status_text, rewarded_points=rewarded_points, new_balance=new_balance)
