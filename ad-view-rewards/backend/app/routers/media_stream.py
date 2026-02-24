import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_viewer
from app.models.user import User
from app.services.storage_service import LocalStorageService

logger = logging.getLogger(__name__)
router = APIRouter()


def _stream_file_chunks(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    with path.open("rb") as file_obj:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk


def _log_forbidden(request: Request, user_id: str, filename: str) -> None:
    client_ip = request.client.host if request.client else ""
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip else None
    logger.warning(
        "signed_url_validation_failed timestamp=%s user_id=%s ip_hash=%s filename=%s",
        datetime.now(timezone.utc).isoformat(),
        user_id,
        ip_hash,
        filename,
    )


@router.get("/ads/{filename}")
def stream_ad_media(
    filename: str,
    request: Request,
    token: str = Query(default=""),
    current_user: User = Depends(get_current_viewer),
) -> StreamingResponse:
    if not token:
        _log_forbidden(request, str(current_user.id), filename)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    file_path = f"/media/ads/{filename}"
    storage = LocalStorageService()
    if not storage.verify_signed_token(token=token, file_path=file_path, user_id=current_user.id):
        _log_forbidden(request, str(current_user.id), filename)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    absolute_path = storage.absolute_path_for_media(file_path)
    if not absolute_path.exists() or not absolute_path.is_file():
        _log_forbidden(request, str(current_user.id), filename)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    return StreamingResponse(_stream_file_chunks(absolute_path), media_type="video/mp4")
